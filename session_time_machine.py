import json
import os
import shutil
import subprocess
import time

import sublime
import sublime_plugin

SETTINGS_FILE = "SessionTimeMachine.sublime-settings"
DEFAULT_INTERVAL_SECONDS = 300
DEFAULT_RETENTION = 200
MIN_INTERVAL_SECONDS = 10
DEFAULT_SYNC_MIN_INTERVAL = 60
DEFAULT_ROLLBACK_LIMIT = 200


def _to_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return value.decode("utf-8", "replace")
    except Exception:
        return str(value)


def _data_dir():
    return os.path.dirname(sublime.packages_path())


def _user_dir():
    return os.path.join(sublime.packages_path(), "User")


def _session_file_path():
    return os.path.join(_data_dir(), "Local", "Session.sublime_session")


def _auto_save_session_file_path():
    return os.path.join(_data_dir(), "Local", "Auto Save Session.sublime_session")


def _settings():
    return sublime.load_settings(SETTINGS_FILE)


def _backup_root():
    settings = _settings()
    custom = settings.get("backup_root")
    if custom:
        return os.path.expanduser(custom)
    return os.path.join(_data_dir(), ".sync_backup")


def _ensure_dir(path):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def _timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def _date_stamp():
    return time.strftime("%Y%m%d")


def _is_under(path, root):
    path = os.path.normcase(os.path.realpath(path))
    root = os.path.normcase(os.path.realpath(root))
    if not root.endswith(os.sep):
        root += os.sep
    return path.startswith(root)


def _cleanup_oldest(folder, keep):
    if keep <= 0:
        return
    entries = []
    for root, _, files in os.walk(folder):
        for name in files:
            entries.append(os.path.join(root, name))

    if len(entries) <= keep:
        return

    entries.sort(key=lambda p: os.path.getmtime(p))
    for path in entries[: len(entries) - keep]:
        try:
            os.remove(path)
        except OSError:
            pass


def _snapshot_file(src_path, category, name_prefix):
    if not os.path.isfile(src_path):
        return

    root = _backup_root()
    folder = os.path.join(root, category, _date_stamp())
    _ensure_dir(folder)

    timestamp = _timestamp()
    base = os.path.basename(src_path)
    backup_name = "{prefix}_{base}_{ts}.bak".format(
        prefix=name_prefix,
        base=base,
        ts=timestamp,
    )
    dest_path = os.path.join(folder, backup_name)

    try:
        shutil.copy2(src_path, dest_path)
    except Exception as exc:
        sublime.status_message("SessionTimeMachine: backup failed ({})".format(exc))
        return

    retention = int(_settings().get("retention_per_type", DEFAULT_RETENTION))
    _cleanup_oldest(folder, retention)


def snapshot_session():
    settings = _settings()
    if settings.get("snapshot_auto_save_session", True):
        _snapshot_file(_auto_save_session_file_path(), "session", "AutoSave")
    if settings.get("snapshot_session_file", True):
        _snapshot_file(_session_file_path(), "session", "Session")
    _maybe_sync_after_snapshot()


def snapshot_user_file(file_path):
    _snapshot_file(file_path, "user", "User")
    _maybe_sync_after_snapshot()


class SessionTimeMachineListener(sublime_plugin.EventListener):
    def on_post_save_async(self, view):
        settings = _settings()
        if not settings.get("enabled", True):
            return
        if not settings.get("backup_on_settings_save", True):
            return

        file_path = view.file_name()
        if not file_path:
            return

        user_dir = _user_dir()
        if not _is_under(file_path, user_dir):
            return

        snapshot_user_file(file_path)


class _SnapshotScheduler(object):
    def __init__(self):
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return

        settings = _settings()
        if settings.get("enabled", True):
            snapshot_session()

        interval = int(settings.get("snapshot_interval_seconds", DEFAULT_INTERVAL_SECONDS))
        if interval < MIN_INTERVAL_SECONDS:
            interval = MIN_INTERVAL_SECONDS

        sublime.set_timeout_async(self._tick, interval * 1000)


_scheduler = _SnapshotScheduler()


class _GitSync(object):
    def __init__(self):
        self._last_sync_ts = 0
        self._busy = False

    def _is_enabled(self):
        settings = _settings()
        return settings.get("sync_enabled", False) and settings.get("sync_backend", "git") == "git"

    def _repo_path(self):
        settings = _settings()
        repo = settings.get("git_repo_path")
        if repo:
            return os.path.expanduser(repo)
        return _backup_root()

    def _git_executable(self):
        return _settings().get("git_executable", "git")

    def _min_interval(self):
        interval = int(_settings().get("sync_min_interval_seconds", DEFAULT_SYNC_MIN_INTERVAL))
        if interval < 0:
            interval = 0
        return interval

    def _can_sync(self):
        if self._busy:
            return False
        now = time.time()
        if now - self._last_sync_ts < self._min_interval():
            return False
        return True

    def _run_git(self, args):
        repo = self._repo_path()
        if not os.path.isdir(repo):
            return 1, "", "repo not found: {}".format(repo)

        cmd = [self._git_executable()] + list(args)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as exc:
            return 1, "", _to_text(exc)

        out, err = proc.communicate()
        return proc.returncode, _to_text(out), _to_text(err)

    def _has_changes(self):
        code, out, err = self._run_git(["status", "--porcelain"])
        if code != 0:
            return False, err or out
        return bool(out.strip()), ""

    def _commit_all(self):
        settings = _settings()
        if not settings.get("git_auto_commit", True):
            return True, ""

        code, out, err = self._run_git(["add", "-A"])
        if code != 0:
            return False, err or out

        has_changes, info = self._has_changes()
        if not has_changes:
            return True, ""
        if info:
            return False, info

        msg = "SessionTimeMachine snapshot {}".format(_timestamp())
        code, out, err = self._run_git(["commit", "-m", msg])
        if code != 0:
            return False, err or out
        return True, ""

    def _pull(self):
        settings = _settings()
        remote = settings.get("git_remote", "origin")
        branch = settings.get("git_branch", "")
        if branch:
            return self._run_git(["pull", remote, branch])
        return self._run_git(["pull", remote])

    def _push(self):
        settings = _settings()
        remote = settings.get("git_remote", "origin")
        branch = settings.get("git_branch", "")
        if branch:
            return self._run_git(["push", remote, branch])
        return self._run_git(["push", remote])

    def pull_async(self):
        if not self._is_enabled():
            return
        if not self._can_sync():
            return
        self._busy = True
        self._last_sync_ts = time.time()
        sublime.set_timeout_async(self._pull_task, 0)

    def push_async(self):
        settings = _settings()
        if not self._is_enabled():
            return
        if not settings.get("git_push_on_snapshot", True):
            return
        if not self._can_sync():
            return
        self._busy = True
        self._last_sync_ts = time.time()
        sublime.set_timeout_async(self._push_task, 0)

    def _pull_task(self):
        try:
            code, out, err = self._pull()
            if code != 0:
                sublime.status_message("SessionTimeMachine: git pull failed ({})".format(err or out))
        finally:
            self._busy = False

    def _push_task(self):
        try:
            ok, info = self._commit_all()
            if not ok:
                sublime.status_message("SessionTimeMachine: git commit failed ({})".format(info))
                return
            code, out, err = self._push()
            if code != 0:
                sublime.status_message("SessionTimeMachine: git push failed ({})".format(err or out))
        finally:
            self._busy = False


_git_sync = _GitSync()


def _maybe_sync_after_snapshot():
    _git_sync.push_async()


def plugin_loaded():
    _scheduler.start()
    settings = _settings()
    if settings.get("sync_pull_on_startup", True):
        _git_sync.pull_async()


def _list_session_snapshots():
    root = os.path.join(_backup_root(), "session")
    entries = []
    if not os.path.isdir(root):
        return entries

    for dirpath, _, files in os.walk(root):
        for name in files:
            if not name.endswith(".bak"):
                continue
            path = os.path.join(dirpath, name)
            ts = os.path.getmtime(path)
            entries.append((ts, name, path))

    entries.sort(key=lambda item: item[0], reverse=True)
    limit = int(_settings().get("rollback_list_limit", DEFAULT_ROLLBACK_LIMIT))
    if limit > 0:
        entries = entries[:limit]
    return entries


def _parse_session_file(path):
    try:
        with open(path, "r") as handle:
            data = handle.read()
        return json.loads(data)
    except Exception as exc:
        sublime.status_message("SessionTimeMachine: parse failed ({})".format(exc))
        return None


def _apply_path_mappings(path):
    settings = _settings()
    mappings = settings.get("path_mappings", [])
    if not isinstance(mappings, list):
        return path
    original = path
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        source = mapping.get("from")
        target = mapping.get("to")
        if not source or not target:
            continue
        source_norm = os.path.normcase(source)
        path_norm = os.path.normcase(path)
        if path_norm.startswith(source_norm):
            return target + original[len(source) :]
    return original


def _extract_buffers(session):
    buffers = []
    if isinstance(session, dict):
        if isinstance(session.get("buffers"), list):
            buffers.extend(session.get("buffers"))
        windows = session.get("windows")
        if isinstance(windows, list):
            for win in windows:
                if isinstance(win, dict) and isinstance(win.get("buffers"), list):
                    buffers.extend(win.get("buffers"))
    return buffers


def _collect_restore_items(session):
    buffers = _extract_buffers(session)
    buffer_by_id = {}
    unnamed_buffers = []

    for buf in buffers:
        if not isinstance(buf, dict):
            continue
        buffer_id = buf.get("buffer_id")
        if buffer_id is not None:
            buffer_by_id[buffer_id] = buf
        if not buf.get("file_name") and buf.get("contents"):
            unnamed_buffers.append(buf)

    file_paths = []
    windows = session.get("windows", [])
    if isinstance(windows, list):
        for win in windows:
            if not isinstance(win, dict):
                continue
            views = win.get("views", [])
            if not isinstance(views, list):
                continue
            for view in views:
                if not isinstance(view, dict):
                    continue
                buffer_id = view.get("buffer_id")
                buf = buffer_by_id.get(buffer_id)
                if buf and buf.get("file_name"):
                    file_paths.append(buf.get("file_name"))
                elif view.get("file_name"):
                    file_paths.append(view.get("file_name"))

    deduped = []
    seen = set()
    for path in file_paths:
        if not path:
            continue
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)

    return deduped, unnamed_buffers


def _restore_buffer_contents(view, contents):
    if view.is_loading():
        sublime.set_timeout(lambda: _restore_buffer_contents(view, contents), 100)
        return
    view.set_read_only(False)
    view.run_command("select_all")
    view.run_command("right_delete")
    view.run_command("insert", {"characters": contents})


def _restore_session_from_snapshot(path):
    session = _parse_session_file(path)
    if not session:
        return

    settings = _settings()
    restore_files = settings.get("rollback_restore_open_files", True)
    restore_buffers = settings.get("rollback_restore_unsaved_buffers", True)

    file_paths, unnamed_buffers = _collect_restore_items(session)
    window = sublime.active_window()
    if not window:
        return

    if restore_files:
        for raw_path in file_paths:
            mapped = _apply_path_mappings(raw_path)
            if os.path.exists(mapped):
                window.open_file(mapped)
            else:
                sublime.status_message("SessionTimeMachine: missing file {}".format(mapped))

    if restore_buffers:
        for buf in unnamed_buffers:
            contents = buf.get("contents")
            if not contents:
                continue
            view = window.new_file()
            name = buf.get("name")
            if name:
                view.set_name(name)
            _restore_buffer_contents(view, contents)


class SessionTimeMachineRollbackCommand(sublime_plugin.WindowCommand):
    def run(self):
        snapshots = _list_session_snapshots()
        if not snapshots:
            sublime.status_message("SessionTimeMachine: no session snapshots found")
            return
        self._snapshots = snapshots

        items = []
        for ts, name, path in snapshots:
            label = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            items.append([label, name])

        self.window.show_quick_panel(items, self._on_select_snapshot)

    def _on_select_snapshot(self, index):
        if index == -1:
            return
        _, _, path = self._snapshots[index]
        sublime.set_timeout_async(lambda: _restore_session_from_snapshot(path), 0)


def plugin_unloaded():
    _scheduler.stop()
