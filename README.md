# SessionTimeMachine

Sublime Text 3 插件：为 Session 提供本地快照、历史回滚、全文检索，并支持可选的 Git 同步。

## 功能
- 定时备份 `Auto Save Session.sublime_session` 与 `Session.sublime_session`。
- 保存 `Packages/User` 下配置文件时自动备份。
- 快照历史回滚：重建打开文件与未保存缓冲区。
- 未保存内容历史检索与快速恢复（SQLite FTS）。
- 可选 Git 同步：启动拉取、快照推送。

## 安装

### Package Control（待提交官方仓库）
发布后可通过 Package Control 安装。

### 手动安装
1. 将 `session_time_machine.py`、`SessionTimeMachine.sublime-settings`、`Default.sublime-commands` 放入 `Packages/User`。
2. 重启 Sublime Text 3。

## 使用
- 回滚：Command Palette → `SessionTimeMachine: Rollback History`
- 搜索：Command Palette → `SessionTimeMachine: Search History`

## 配置
编辑 `SessionTimeMachine.sublime-settings`：

基础：
- `enabled`: 是否启用。
- `backup_on_settings_save`: 保存 User 配置时是否备份。
- `snapshot_interval_seconds`: Session 快照间隔（秒）。
- `retention_per_type`: 每类快照保留数量。
- `backup_root`: 备份目录（为空则使用 Data 目录下 `.sync_backup`）。
- `snapshot_auto_save_session`: 是否备份 `Auto Save Session.sublime_session`。
- `snapshot_session_file`: 是否备份 `Session.sublime_session`。

回滚：
- `rollback_list_limit`: 回滚列表展示的最大快照数量。
- `rollback_restore_open_files`: 是否恢复历史打开文件。
- `rollback_restore_unsaved_buffers`: 是否恢复未保存缓冲区。
- `rollback_open_missing_files`: 缺失文件是否也尝试打开。
- `path_mappings`: 跨平台路径映射。
  例：`[{"from": "C:\\Projects\\", "to": "/home/user/projects/"}]`

索引与搜索：
- `index_enabled`: 是否启用历史索引。
- `index_db_path`: SQLite 数据库路径（为空则使用 `backup_root/index.sqlite`）。
- `index_max_rows`: 索引最大行数（超过后删除最旧记录）。
- `search_result_limit`: 搜索结果最大条数。

Git 同步：
- `sync_enabled`: 是否启用同步。
- `sync_backend`: 目前仅支持 `git`。
- `sync_min_interval_seconds`: 最小同步间隔（秒）。
- `git_executable`: Git 命令路径或别名。
- `git_repo_path`: Git 仓库路径（为空则使用 `backup_root`）。
- `git_remote`: 远端名。
- `git_branch`: 远端分支（空则使用 Git 默认分支）。
- `git_auto_commit`: 快照后自动 `git add/commit`。
- `git_pull_on_startup`: 启动时拉取。
- `git_push_on_snapshot`: 快照后推送。

## 备份目录结构
- `.sync_backup/session/YYYYMMDD`：Session 快照（按日期分目录）。
- `.sync_backup/user/YYYYMMDD`：User 配置文件快照（按日期分目录）。

## 已知限制
- 回滚不恢复窗口布局与面板状态。
- 仅对未保存缓冲区做全文索引。

## 贡献
欢迎提交 Issue 和 PR。

## 许可
MIT License。详见 `LICENSE`。
