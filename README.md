# SessionTimeMachine

Sublime Text 3 插件原型：提供 Session 本地快照、User 配置备份、回滚、历史搜索与可选 Git 同步。

## 功能（当前阶段）
- 定时备份 `Auto Save Session.sublime_session` 与 `Session.sublime_session` 到本地快照目录。
- 保存 `Packages/User` 下配置文件时自动备份。
- 按保留数量自动清理最旧快照。
- 回滚历史：从快照重建打开文件与未保存缓冲区。
- 历史搜索：索引未保存缓冲区内容并支持查询恢复。
- 可选 Git 同步：启动时拉取，快照后推送。

## 安装与使用
1. 将 `session_time_machine.py`、`SessionTimeMachine.sublime-settings`、`Default.sublime-commands` 放入 Sublime Text 3 的 `Packages/User` 目录。
2. 重启 Sublime Text 3。
3. 默认每 5 分钟生成一次 Session 快照。

## 回滚使用
打开 Command Palette，执行 `SessionTimeMachine: Rollback History`，选择一个快照即可恢复。

## 搜索使用
打开 Command Palette，执行 `SessionTimeMachine: Search History`，输入关键词后选择结果即可恢复内容。

## 配置
编辑 `SessionTimeMachine.sublime-settings`：
- `enabled`: 是否启用。
- `backup_on_settings_save`: 保存 User 配置时是否备份。
- `snapshot_interval_seconds`: Session 快照间隔（秒）。
- `retention_per_type`: 每类快照保留数量。
- `backup_root`: 备份目录（为空则使用 Data 目录下 `.sync_backup`）。
- `snapshot_auto_save_session`: 是否备份 `Auto Save Session.sublime_session`。
- `snapshot_session_file`: 是否备份 `Session.sublime_session`。

回滚相关：
- `rollback_list_limit`: 回滚列表展示的最大快照数量。
- `rollback_restore_open_files`: 是否恢复历史打开文件。
- `rollback_restore_unsaved_buffers`: 是否恢复未保存缓冲区。
- `rollback_open_missing_files`: 缺失文件是否也尝试打开。
- `path_mappings`: 跨平台路径映射。例：`[{"from": "C:\\Projects\\", "to": "/home/user/projects/"}]`。

索引与搜索相关：
- `index_enabled`: 是否启用历史索引。
- `index_db_path`: SQLite 数据库路径（为空则使用 `backup_root/index.sqlite`）。
- `index_max_rows`: 索引最大行数（超过后删除最旧记录）。
- `search_result_limit`: 搜索结果最大条数。

Git 同步相关：
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

## 下一步
- 索引性能优化（去重、增量更新、更多字段）。
