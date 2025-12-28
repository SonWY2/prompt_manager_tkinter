# Prompt Manager - Architecture Document

## Project Overview

**Product Name:** Prompt Manager (LLM 프롬프트 관리 프로그램)

**Purpose:** A desktop application for managing, versioning, and testing LLM prompts efficiently. Users can organize prompts by tasks, manage versions, use template variables, and execute prompts against various LLM APIs.

**Tech Stack:**
- Language: Python 3.10+
- GUI Framework: Tkinter with ttk for modern widgets
- Data Storage: JSON files (lightweight, no external DB required)
- API Integration: OpenAI-compatible REST APIs

**Core Value Proposition:**
- Structured prompt organization by Task and Version
- Template variable management with dynamic substitution
- Direct LLM API execution from UI
- Version control and execution history tracking

---

## Functional Requirements (Must-haves)

### 1. Task Management
- **Create Task:** User can create a new task with a unique name
- **List Tasks:** Display all tasks in a sidebar, sorted by recent modification
- **Select Task:** Click to view/edit task details
- **Delete Task:** Remove task with cascade deletion of all versions and results
- **Edit Task Name:** Rename existing tasks

### 2. Prompt Editing & Versioning
- **Three-Part Editor:**
  - Description: Metadata about the prompt version
  - System Prompt: Role definition for LLM
  - User Prompt: Main instruction with `{{variable}}` template support
- **Create New Version:** Save current state as a new version snapshot
- **Version Navigation:** Browse and switch between versions via timeline
- **Auto-save:** Persist changes automatically on focus loss

### 3. Template Variables
- **Auto-extraction:** Parse `{{variable_name}}` patterns from prompts
- **Value Assignment:** Set default values at Task level
- **Variable List Display:** Show all extracted variables with input fields
- **Preview:** Display final rendered prompt with substituted values

### 4. LLM Execution
- **Endpoint Configuration:** Store LLM API credentials (name, base URL, API key, model)
- **Run Prompt:** Execute current version with variable substitution
- **Display Response:** Show LLM output in dedicated panel
- **Error Handling:** Show timeout, API errors gracefully

### 5. Execution History
- **Save Results:** Store all executions with timestamp, inputs, outputs
- **View History:** List past executions for selected version
- **Detail View:** Show full request/response for selected history item

---

## User Interface Spec (Rough Sketch)

### Layout Structure
```
+----------------------------------------------------------+
|  Menu Bar [File | Task | View | Settings]                |
+----------------------------------------------------------+
|                                                          |
|  +-------------+  +----------------------------------+   |
|  | Task List   |  | Main Work Area                  |   |
|  | (Sidebar)   |  | +------------------------------+ |   |
|  |             |  | | Version Timeline            | |   |
|  | - Task 1    |  | +------------------------------+ |   |
|  | - Task 2    |  |                                  |   |
|  | - Task 3    |  | [Tabs: Edit | Variables | Run]   |   |
|  |             |  |                                  |   |
|  | [+ New]     |  | Edit Tab:                        |   |
|  |             |  | - Description (Entry)            |   |
|  |             |  | - System Prompt (Text)           |   |
|  |             |  | - User Prompt (Text)             |   |
|  |             |  |                                  |   |
|  |             |  | Variables Tab:                   |   |
|  |             |  | - var1: [value input]            |   |
|  |             |  | - var2: [value input]            |   |
|  |             |  |                                  |   |
|  |             |  | Run Tab:                         |   |
|  |             |  | - [Execute Button]               |   |
|  |             |  | - Response Display               |   |
|  |             |  | - History List                   |   |
|  +-------------+  +----------------------------------+   |
|                                                          |
+----------------------------------------------------------+
|  Status Bar: [Auto-save status | Current Model]          |
+----------------------------------------------------------+
```

### Key UI Elements
1. **Left Sidebar:** Listbox of tasks with scrollbar
2. **Version Timeline:** Horizontal list/buttons showing v1, v2, v3...
3. **Tab Control:** Notebook widget with 3 tabs (Edit, Variables, Run)
4. **Text Widgets:** ScrolledText for multi-line prompt editing
5. **Button Actions:** New Task, Delete Task, New Version, Execute Prompt

---

## Data Structures & Logic

### Data Model

#### Task
```python
{
  "id": "unique_task_id",
  "name": "Task Name",
  "created_at": "2025-12-28T10:00:00",
  "modified_at": "2025-12-28T11:30:00",
  "variables": {
    "variable_name": "default_value"
  },
  "versions": [...]  # List of Version objects
}
```

#### Version
```python
{
  "version_id": "v1",
  "description": "Initial version",
  "system_prompt": "You are a helpful assistant",
  "user_prompt": "Write about {{topic}}",
  "created_at": "2025-12-28T10:00:00"
}
```

#### Result
```python
{
  "result_id": "unique_result_id",
  "version_id": "v1",
  "executed_at": "2025-12-28T11:00:00",
  "inputs": {"topic": "AI"},
  "rendered_prompt": "Write about AI",
  "response": "AI stands for...",
  "model": "gpt-4",
  "tokens": {"input": 10, "output": 50}
}
```

#### LLM Endpoint
```python
{
  "name": "OpenAI GPT-4",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4",
  "active": true
}
```

### Core Logic Functions

1. **Variable Extraction**
   - Regex: `\{\{([a-zA-Z0-9_-]+)\}\}`
   - Extract unique variable names from system_prompt + user_prompt
   - Return list of variable names

2. **Prompt Rendering**
   - Take template string and variables dict
   - Replace all `{{var}}` with corresponding value
   - Return final rendered string

3. **LLM API Call**
   - Construct request payload: `{"model": "...", "messages": [...]}`
   - POST to endpoint/chat/completions
   - Parse response and extract content
   - Handle errors (timeout, 401, 429, 500)

4. **Data Persistence**
   - Save/Load tasks from JSON file: `data/tasks.json`
   - Save/Load config from: `data/config.json`
   - Auto-save on every significant change

### File Structure
```
prompt_manager_claude_code/
├── src/
│   └── main.py          # Main application code
├── data/
│   ├── tasks.json       # All tasks, versions, results
│   └── config.json      # LLM endpoints, settings
├── docs/
│   └── architecture.md  # This file
└── CLAUDE.md            # Project rules
```

---

## Edge Cases & Error Handling

1. **Empty Task Name:** Show validation error, prevent creation
2. **Duplicate Task Name:** Allow (add timestamp suffix) or warn user
3. **Missing API Key:** Show clear error message, guide to settings
4. **API Timeout:** Show timeout message, don't freeze UI
5. **Invalid Variable Name:** Ignore variables with special characters
6. **Network Failure:** Catch connection errors, show user-friendly message
7. **Corrupted JSON Data:** Backup existing file, create new empty state
8. **Large Response:** Truncate display if response > 10000 chars

---

## Data Flow Summary

1. **User creates Task** → Save to tasks.json → Update sidebar
2. **User edits prompt** → Extract variables → Auto-save after 1 sec delay
3. **User sets variable values** → Store in Task.variables → Enable Run button
4. **User clicks Run** → Render prompt → Call LLM API → Display response → Save to Result
5. **User switches version** → Load version data → Update editor UI
6. **User views history** → Filter results by version_id → Display in list

---

## Non-Functional Requirements

- **Performance:** UI should remain responsive during API calls (use threading)
- **Usability:** Clear visual feedback for all actions (loading spinners, status messages)
- **Reliability:** Auto-save every 2 seconds to prevent data loss
- **Maintainability:** Separate UI code from business logic (MVC pattern)
- **Security:** Store API keys securely (consider encryption in future)

---

## Implementation Priority

### Phase 1 (MVP)
1. Basic Task CRUD
2. Single version prompt editor
3. Variable extraction and display
4. Simple LLM execution (hardcoded endpoint)
5. Basic result display

### Phase 2 (Full Features)
6. Multiple version support with timeline
7. Endpoint management UI
8. Execution history with persistence
9. Auto-save functionality
10. Error handling and validation

### Phase 3 (Polish)
11. Variable preview/rendering
12. Better UI styling
13. Keyboard shortcuts
14. Export/import functionality

**For this implementation, we will target Phase 1 + Phase 2 core features.**

---

## Success Criteria

The application is successful if:
1. User can create multiple tasks and organize prompts
2. User can define variables and see them extracted automatically
3. User can execute prompts and see LLM responses
4. All data persists between sessions
5. No crashes on normal operations
6. Clear error messages for all failure scenarios

---

## Detailed UI Layout Specification (Tkinter Implementation)

### Widget Hierarchy Tree

```
Root (tk.Tk) - "Prompt Manager"
├── MenuBar (tk.Menu)
│   ├── File Menu
│   │   ├── New Task (Command)
│   │   ├── Save All (Command)
│   │   └── Exit (Command)
│   ├── Settings Menu
│   │   └── Configure Endpoints (Command)
│   └── Help Menu
│       └── About (Command)
├── MainContainer (ttk.Frame) [grid, fill=both, expand=True]
│   ├── LeftPanel (ttk.Frame) [grid, column=0, sticky=NS]
│   │   ├── TaskListLabel (ttk.Label) text="Tasks"
│   │   ├── TaskListbox (tk.Listbox) [scrollable]
│   │   │   └── TaskScrollbar (ttk.Scrollbar)
│   │   ├── ButtonFrame (ttk.Frame)
│   │   │   ├── NewTaskButton (ttk.Button) text="+ New Task"
│   │   │   └── DeleteTaskButton (ttk.Button) text="Delete"
│   │   └── RenameFrame (ttk.Frame)
│   │       ├── RenameEntry (ttk.Entry)
│   │       └── RenameButton (ttk.Button) text="Rename"
│   └── RightPanel (ttk.Frame) [grid, column=1, sticky=NSEW]
│       ├── VersionFrame (ttk.Frame) [pack, fill=X]
│       │   ├── VersionLabel (ttk.Label) text="Versions:"
│       │   ├── VersionButtonFrame (ttk.Frame) [horizontal layout]
│       │   │   └── VersionButtons (ttk.Button[]) text="v1", "v2", "v3"...
│       │   └── NewVersionButton (ttk.Button) text="+ New Version"
│       └── ContentNotebook (ttk.Notebook) [pack, fill=both, expand=True]
│           ├── EditTab (ttk.Frame)
│           │   ├── DescFrame (ttk.LabelFrame) text="Description"
│           │   │   └── DescEntry (ttk.Entry)
│           │   ├── SystemFrame (ttk.LabelFrame) text="System Prompt"
│           │   │   └── SystemText (scrolledtext.ScrolledText) height=8
│           │   └── UserFrame (ttk.LabelFrame) text="User Prompt"
│           │       └── UserText (scrolledtext.ScrolledText) height=12
│           ├── VariablesTab (ttk.Frame)
│           │   ├── VarLabel (ttk.Label) text="Template Variables"
│           │   ├── VarListFrame (ttk.Frame) [scrollable container]
│           │   │   └── VarEntries (Grid of ttk.Label + ttk.Entry pairs)
│           │   └── PreviewFrame (ttk.LabelFrame) text="Preview"
│           │       └── PreviewText (scrolledtext.ScrolledText) state=disabled
│           └── RunTab (ttk.Frame)
│               ├── ExecuteFrame (ttk.Frame)
│               │   ├── ExecuteButton (ttk.Button) text="Run Prompt"
│               │   └── StatusLabel (ttk.Label) text="Ready"
│               ├── ResponseFrame (ttk.LabelFrame) text="Response"
│               │   └── ResponseText (scrolledtext.ScrolledText) state=disabled
│               └── HistoryFrame (ttk.LabelFrame) text="Execution History"
│                   ├── HistoryListbox (tk.Listbox)
│                   │   └── HistoryScrollbar (ttk.Scrollbar)
│                   └── ViewDetailsButton (ttk.Button) text="View Details"
└── StatusBar (ttk.Frame) [grid, sticky=EW]
    ├── SaveStatusLabel (ttk.Label) text="Saved"
    └── ModelLabel (ttk.Label) text="Model: None"
```

### Layout Manager Strategy

#### Grid Layout (Main Structure)
```python
# Root window configuration
root.columnconfigure(0, weight=0)  # Left panel - fixed width
root.columnconfigure(1, weight=1)  # Right panel - expandable
root.rowconfigure(0, weight=1)     # Main container - expandable
root.rowconfigure(1, weight=0)     # Status bar - fixed height

# MainContainer
main_container.grid(row=0, column=0, columnspan=2, sticky="NSEW")
status_bar.grid(row=1, column=0, columnspan=2, sticky="EW")

# Left Panel (Fixed 250px width)
left_panel.grid(row=0, column=0, sticky="NS", padx=5, pady=5)
left_panel.config(width=250)

# Right Panel (Expandable)
right_panel.grid(row=0, column=1, sticky="NSEW", padx=5, pady=5)
right_panel.columnconfigure(0, weight=1)
right_panel.rowconfigure(1, weight=1)
```

#### Pack Layout (Nested Components)
```python
# Version Frame - horizontal layout
version_frame.pack(fill="x", padx=10, pady=5)

# Content Notebook - fills remaining space
content_notebook.pack(fill="both", expand=True, padx=10, pady=5)

# Edit Tab components - vertical stacking
desc_frame.pack(fill="x", padx=5, pady=5)
system_frame.pack(fill="both", expand=True, padx=5, pady=5)
user_frame.pack(fill="both", expand=True, padx=5, pady=5)
```

### Widget Specifications

#### Task Listbox
```python
task_listbox = tk.Listbox(
    left_panel,
    selectmode=tk.SINGLE,
    height=20,
    font=("Arial", 10),
    activestyle="dotbox"
)
# Callback: on_task_select(event)
```

#### ScrolledText Widgets
```python
system_text = scrolledtext.ScrolledText(
    system_frame,
    height=8,
    width=60,
    font=("Consolas", 10),
    wrap=tk.WORD
)
# Callbacks: on_text_change(event), on_focus_out(event)
```

#### Version Buttons (Dynamic)
```python
# Generated dynamically based on versions list
for idx, version in enumerate(versions):
    btn = ttk.Button(
        version_button_frame,
        text=f"v{idx+1}",
        width=5,
        command=lambda v=version: self.load_version(v)
    )
    btn.pack(side=tk.LEFT, padx=2)
    # Highlight current version with different style
```

#### Variable Entry Grid
```python
# Dynamic grid based on extracted variables
row = 0
for var_name in extracted_variables:
    label = ttk.Label(var_list_frame, text=f"{var_name}:")
    label.grid(row=row, column=0, sticky="E", padx=5, pady=3)

    entry = ttk.Entry(var_list_frame, width=40)
    entry.grid(row=row, column=1, sticky="EW", padx=5, pady=3)
    entry.bind("<FocusOut>", lambda e, v=var_name: self.save_variable(v, e.widget.get()))
    row += 1
```

### Styling & Theme

```python
# Use ttk themed widgets for modern look
style = ttk.Style()
style.theme_use('clam')  # or 'vista' on Windows

# Custom colors
BACKGROUND = "#f5f5f5"
ACCENT = "#007acc"
TEXT_COLOR = "#333333"

# Configure styles
style.configure("TFrame", background=BACKGROUND)
style.configure("TLabel", background=BACKGROUND, foreground=TEXT_COLOR)
style.configure("TButton", padding=6)
style.map("TButton",
    background=[('active', ACCENT), ('!active', '#e1e1e1')])
```

### Responsiveness Configuration

```python
# Make text widgets resize with window
system_frame.columnconfigure(0, weight=1)
system_frame.rowconfigure(0, weight=1)
user_frame.columnconfigure(0, weight=1)
user_frame.rowconfigure(0, weight=1)

# Variables tab scrollable
var_list_frame.columnconfigure(1, weight=1)

# Run tab response area expandable
response_frame.columnconfigure(0, weight=1)
response_frame.rowconfigure(0, weight=1)
```

### Key Bindings & Shortcuts

```python
# Keyboard shortcuts
root.bind("<Control-n>", lambda e: self.create_new_task())
root.bind("<Control-s>", lambda e: self.save_all())
root.bind("<F5>", lambda e: self.execute_prompt())

# Text widget auto-save on idle
system_text.bind("<KeyRelease>", lambda e: self.schedule_autosave())
user_text.bind("<KeyRelease>", lambda e: self.schedule_autosave())
```

### Padding & Spacing Standards

- **Outer padding:** 10px for major frames
- **Inner padding:** 5px for nested widgets
- **Button spacing:** 2-5px horizontal gap
- **LabelFrame padding:** 8px internal padding
- **Text widget margins:** 3px on all sides

### Visual Feedback Elements

1. **Loading State:** Change Execute button text to "Running..." and disable
2. **Save State:** Update status label: "Saving..." → "Saved" → "Error"
3. **Selected Version:** Highlight active version button with different background
4. **Selected Task:** Listbox selection with accent color background
5. **Empty State:** Show placeholder text "No tasks yet. Create one to get started."

### Dialog Windows

#### Settings Dialog (Endpoint Configuration)
```python
settings_dialog = tk.Toplevel(root)
settings_dialog.title("LLM Endpoint Settings")
settings_dialog.geometry("500x400")
settings_dialog.transient(root)  # Modal

# Fields: Name, Base URL, API Key, Model, Active checkbox
# Buttons: Save, Cancel
```

#### History Detail Dialog
```python
detail_dialog = tk.Toplevel(root)
detail_dialog.title("Execution Details")
detail_dialog.geometry("700x600")

# Display: Timestamp, Model, Input Variables, Rendered Prompt, Response
# Button: Close
```

---

## Implementation Notes

1. **Separation of Concerns:**
   - `setup_ui()` - Creates all widgets
   - `bind_events()` - Attaches event handlers
   - Business logic in separate methods

2. **State Management:**
   - `current_task: Optional[Task]` - Currently selected task
   - `current_version: Optional[Version]` - Currently loaded version
   - `autosave_timer: Optional[str]` - Timer ID for auto-save

3. **Thread Safety:**
   - LLM API calls in separate thread
   - Use `root.after()` to update UI from thread
   - Lock shared data structures if needed

4. **Performance:**
   - Lazy load history details (don't load all at startup)
   - Limit history display to last 50 executions
   - Use virtual events for complex state updates
