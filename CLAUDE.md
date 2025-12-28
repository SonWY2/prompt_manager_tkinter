# Claude Code Project Rules

## Tech Stack
- **Language**: Python 3.10+
- **GUI Framework**: Tkinter (Standard Library), `tkinter.ttk` for modern widgets.
- **Style Guide**: PEP 8 compatible.

## Coding Conventions
- **Modular Design**: GUI logic and Business logic must be separated (MVC Pattern preferred).
- **Error Handling**: All user inputs must be validated. Use `try-except` blocks for I/O operations.
- **Comments**: Write docstrings for classes and functions.
- **Type Hinting**: Use Python type hints strictly.

## Workflow
- Always update `docs/architecture.md` before writing code.
- If a validation step fails, read the critique and fix the issue before proceeding.