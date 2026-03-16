# Contributing

Thanks for your interest in contributing to SessionTimeMachine.

## How to Contribute
- Open an issue for bugs or feature requests with clear steps to reproduce.
- Submit pull requests with focused changes and a concise description.
- Keep changes compatible with Sublime Text 3 (Python 3.3).

## Development Notes
- Avoid blocking the UI thread; use `sublime.set_timeout_async` for I/O.
- Keep dependencies minimal; prefer stdlib only.
- Ensure new features are configurable via `SessionTimeMachine.sublime-settings`.

## Code Style
- Use clear, descriptive names.
- Keep functions small and focused.
- Prefer explicit error handling with user-facing `status_message`.

## License
By contributing, you agree that your contributions will be licensed under the MIT License.

