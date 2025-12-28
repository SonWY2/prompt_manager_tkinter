"""
Prompt Manager - LLM Prompt Management Application
A desktop application for managing, versioning, and testing LLM prompts.
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import threading
import urllib.request
import urllib.error


# ============================================================================
# Data Models
# ============================================================================

class Version:
    """Represents a single version of a prompt."""

    def __init__(self, version_id: str, description: str = "",
                 system_prompt: str = "", user_prompt: str = "",
                 created_at: Optional[str] = None):
        self.version_id = version_id
        self.description = description
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Version':
        return Version(
            version_id=data.get("version_id", "v1"),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            user_prompt=data.get("user_prompt", ""),
            created_at=data.get("created_at")
        )


class Result:
    """Represents an execution result."""

    def __init__(self, result_id: str, version_id: str, executed_at: str,
                 inputs: Dict[str, str], rendered_prompt: str,
                 response: str, model: str):
        self.result_id = result_id
        self.version_id = version_id
        self.executed_at = executed_at
        self.inputs = inputs
        self.rendered_prompt = rendered_prompt
        self.response = response
        self.model = model

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "version_id": self.version_id,
            "executed_at": self.executed_at,
            "inputs": self.inputs,
            "rendered_prompt": self.rendered_prompt,
            "response": self.response,
            "model": self.model
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Result':
        return Result(
            result_id=data.get("result_id", ""),
            version_id=data.get("version_id", ""),
            executed_at=data.get("executed_at", ""),
            inputs=data.get("inputs", {}),
            rendered_prompt=data.get("rendered_prompt", ""),
            response=data.get("response", ""),
            model=data.get("model", "")
        )


class Task:
    """Represents a task containing multiple versions."""

    def __init__(self, task_id: str, name: str, created_at: Optional[str] = None,
                 modified_at: Optional[str] = None, variables: Optional[Dict[str, str]] = None,
                 versions: Optional[List[Version]] = None, results: Optional[List[Result]] = None):
        self.task_id = task_id
        self.name = name
        self.created_at = created_at or datetime.now().isoformat()
        self.modified_at = modified_at or datetime.now().isoformat()
        self.variables = variables or {}
        self.versions = versions or [Version("v1", "Initial version")]
        self.results = results or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "variables": self.variables,
            "versions": [v.to_dict() for v in self.versions],
            "results": [r.to_dict() for r in self.results]
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        versions = [Version.from_dict(v) for v in data.get("versions", [])]
        results = [Result.from_dict(r) for r in data.get("results", [])]
        return Task(
            task_id=data.get("id", ""),
            name=data.get("name", ""),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
            variables=data.get("variables", {}),
            versions=versions if versions else [Version("v1", "Initial version")],
            results=results
        )


class Endpoint:
    """Represents an LLM API endpoint configuration."""

    def __init__(self, name: str, base_url: str, api_key: str,
                 model: str, active: bool = False):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.active = active

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "active": self.active
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Endpoint':
        return Endpoint(
            name=data.get("name", ""),
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            model=data.get("model", ""),
            active=data.get("active", False)
        )


# ============================================================================
# Business Logic
# ============================================================================

class PromptManager:
    """Core business logic for managing prompts."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self.config_file = self.data_dir / "config.json"
        self.tasks: List[Task] = []
        self.endpoints: List[Endpoint] = []
        self.load_data()

    def load_data(self):
        """Load tasks and configuration from JSON files."""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(t) for t in data]
        except Exception as e:
            print(f"Error loading tasks: {e}")
            self.tasks = []

        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.endpoints = [Endpoint.from_dict(e) for e in data.get("endpoints", [])]
        except Exception as e:
            print(f"Error loading config: {e}")
            self.endpoints = []

    def save_tasks(self):
        """Save tasks to JSON file."""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tasks: {e}")
            raise

    def save_config(self):
        """Save configuration to JSON file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config = {"endpoints": [e.to_dict() for e in self.endpoints]}
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
            raise

    def create_task(self, name: str) -> Task:
        """Create a new task."""
        task_id = f"task_{len(self.tasks) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task = Task(task_id=task_id, name=name)
        self.tasks.append(task)
        self.save_tasks()
        return task

    def delete_task(self, task: Task):
        """Delete a task."""
        if task in self.tasks:
            self.tasks.remove(task)
            self.save_tasks()

    def rename_task(self, task: Task, new_name: str):
        """Rename a task."""
        task.name = new_name
        task.modified_at = datetime.now().isoformat()
        self.save_tasks()

    def create_version(self, task: Task, description: str = "") -> Version:
        """Create a new version for a task."""
        version_num = len(task.versions) + 1
        version = Version(version_id=f"v{version_num}", description=description)
        task.versions.append(version)
        task.modified_at = datetime.now().isoformat()
        self.save_tasks()
        return version

    def extract_variables(self, text: str) -> List[str]:
        """Extract variable names from template text."""
        pattern = r'\{\{([a-zA-Z0-9_-]+)\}\}'
        matches = re.findall(pattern, text)
        return list(set(matches))

    def render_prompt(self, template: str, variables: Dict[str, str]) -> str:
        """Render a template with variable substitution."""
        result = template
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", var_value)
        return result

    def execute_llm(self, system_prompt: str, user_prompt: str,
                    endpoint: Endpoint) -> str:
        """Execute LLM API call."""
        url = f"{endpoint.base_url.rstrip('/')}/chat/completions"

        payload = {
            "model": endpoint.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {endpoint.api_key}"
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_msg}")
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")

    def save_result(self, task: Task, version: Version, inputs: Dict[str, str],
                    rendered_prompt: str, response: str, model: str):
        """Save execution result."""
        result_id = f"result_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        result = Result(
            result_id=result_id,
            version_id=version.version_id,
            executed_at=datetime.now().isoformat(),
            inputs=inputs,
            rendered_prompt=rendered_prompt,
            response=response,
            model=model
        )
        task.results.append(result)
        self.save_tasks()

    def get_active_endpoint(self) -> Optional[Endpoint]:
        """Get the active endpoint."""
        for endpoint in self.endpoints:
            if endpoint.active:
                return endpoint
        return None


# ============================================================================
# GUI Application
# ============================================================================

class PromptManagerApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("Prompt Manager")
        self.geometry("1200x800")

        # Business logic
        self.manager = PromptManager()

        # State
        self.current_task: Optional[Task] = None
        self.current_version: Optional[Version] = None
        self.autosave_timer: Optional[str] = None

        # Setup UI
        self.setup_ui()
        self.bind_events()
        self.refresh_task_list()

    def setup_ui(self):
        """Create all UI widgets."""
        # Menu bar
        self.setup_menu()

        # Main container
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        # Left panel (Task list)
        self.setup_left_panel()

        # Right panel (Main work area)
        self.setup_right_panel()

        # Status bar
        self.setup_status_bar()

    def setup_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Task", command=self.create_new_task)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure Endpoints", command=self.open_settings_dialog)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_left_panel(self):
        """Create left sidebar with task list."""
        left_panel = ttk.Frame(self, width=250)
        left_panel.grid(row=0, column=0, sticky="NS", padx=5, pady=5)
        left_panel.grid_propagate(False)

        # Task list label
        ttk.Label(left_panel, text="Tasks", font=("Arial", 12, "bold")).pack(pady=5)

        # Task listbox with scrollbar
        listbox_frame = ttk.Frame(left_panel)
        listbox_frame.pack(fill="both", expand=True, pady=5)

        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")

        self.task_listbox = tk.Listbox(
            listbox_frame,
            selectmode=tk.SINGLE,
            font=("Arial", 10),
            yscrollcommand=scrollbar.set
        )
        self.task_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.task_listbox.yview)

        # Button frame
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill="x", pady=5)

        ttk.Button(button_frame, text="+ New Task", command=self.create_new_task).pack(
            side="left", padx=2
        )
        ttk.Button(button_frame, text="Delete", command=self.delete_selected_task).pack(
            side="left", padx=2
        )

        # Rename frame
        rename_frame = ttk.Frame(left_panel)
        rename_frame.pack(fill="x", pady=5)

        self.rename_entry = ttk.Entry(rename_frame)
        self.rename_entry.pack(side="left", fill="x", expand=True, padx=2)

        ttk.Button(rename_frame, text="Rename", command=self.rename_selected_task).pack(
            side="left", padx=2
        )

        self.left_panel = left_panel

    def setup_right_panel(self):
        """Create right panel with version management and tabs."""
        right_panel = ttk.Frame(self)
        right_panel.grid(row=0, column=1, sticky="NSEW", padx=5, pady=5)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        # Version frame
        self.setup_version_frame(right_panel)

        # Content notebook
        self.setup_content_notebook(right_panel)

        self.right_panel = right_panel

    def setup_version_frame(self, parent):
        """Create version timeline."""
        version_frame = ttk.Frame(parent)
        version_frame.grid(row=0, column=0, sticky="EW", padx=10, pady=5)

        ttk.Label(version_frame, text="Versions:", font=("Arial", 10)).pack(side="left", padx=5)

        self.version_button_frame = ttk.Frame(version_frame)
        self.version_button_frame.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(version_frame, text="+ New Version", command=self.create_new_version).pack(
            side="right", padx=5
        )

    def setup_content_notebook(self, parent):
        """Create tabbed content area."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky="NSEW", padx=10, pady=5)

        # Edit tab
        self.setup_edit_tab()

        # Variables tab
        self.setup_variables_tab()

        # Run tab
        self.setup_run_tab()

    def setup_edit_tab(self):
        """Create edit tab with prompt editors."""
        edit_tab = ttk.Frame(self.notebook)
        self.notebook.add(edit_tab, text="Edit")

        # Description
        desc_frame = ttk.LabelFrame(edit_tab, text="Description")
        desc_frame.pack(fill="x", padx=5, pady=5)
        self.desc_entry = ttk.Entry(desc_frame)
        self.desc_entry.pack(fill="x", padx=5, pady=5)

        # PanedWindow for resizable prompts
        paned_window = tk.PanedWindow(edit_tab, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # System prompt
        system_frame = ttk.LabelFrame(paned_window, text="System Prompt")
        self.system_text = scrolledtext.ScrolledText(
            system_frame,
            height=8,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.system_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure text widget tags for highlighting
        self.system_text.tag_configure("placeholder", background="#ffffcc", foreground="#0066cc", font=("Consolas", 10, "bold"))

        paned_window.add(system_frame, minsize=100)

        # User prompt
        user_frame = ttk.LabelFrame(paned_window, text="User Prompt")
        self.user_text = scrolledtext.ScrolledText(
            user_frame,
            height=12,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.user_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Configure text widget tags for highlighting
        self.user_text.tag_configure("placeholder", background="#ffffcc", foreground="#0066cc", font=("Consolas", 10, "bold"))

        paned_window.add(user_frame, minsize=100)

    def setup_variables_tab(self):
        """Create variables tab."""
        var_tab = ttk.Frame(self.notebook)
        self.notebook.add(var_tab, text="Variables")

        # Left-Right split layout
        paned_window = tk.PanedWindow(var_tab, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Variable inputs
        left_panel = ttk.Frame(paned_window)

        ttk.Label(left_panel, text="Template Variables", font=("Arial", 11, "bold")).pack(
            pady=10
        )

        # Scrollable variable list
        var_container = ttk.Frame(left_panel)
        var_container.pack(fill="both", expand=True, padx=5)

        var_canvas = tk.Canvas(var_container, highlightthickness=0)
        var_scrollbar = ttk.Scrollbar(var_container, orient="vertical", command=var_canvas.yview)
        self.var_list_frame = ttk.Frame(var_canvas)

        # Update scroll region when frame size changes
        def on_frame_configure(event):
            var_canvas.configure(scrollregion=var_canvas.bbox("all"))

        self.var_list_frame.bind("<Configure>", on_frame_configure)

        # Create window for the frame
        var_canvas.create_window((0, 0), window=self.var_list_frame, anchor="nw", width=var_canvas.winfo_reqwidth())

        # Update canvas width when it changes
        def on_canvas_configure(event):
            var_canvas.itemconfig(var_canvas.find_withtag("all")[0], width=event.width)

        var_canvas.bind("<Configure>", on_canvas_configure)

        var_canvas.configure(yscrollcommand=var_scrollbar.set)

        # Mouse wheel binding for scrolling (only when mouse is over the canvas)
        def on_mousewheel(event):
            var_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def on_mousewheel_linux(event):
            if event.num == 4:
                var_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                var_canvas.yview_scroll(1, "units")

        def bind_mousewheel(event):
            var_canvas.bind("<MouseWheel>", on_mousewheel)  # Windows/Mac
            var_canvas.bind("<Button-4>", on_mousewheel_linux)  # Linux scroll up
            var_canvas.bind("<Button-5>", on_mousewheel_linux)  # Linux scroll down

        def unbind_mousewheel(event):
            var_canvas.unbind("<MouseWheel>")
            var_canvas.unbind("<Button-4>")
            var_canvas.unbind("<Button-5>")

        var_canvas.bind("<Enter>", bind_mousewheel)
        var_canvas.bind("<Leave>", unbind_mousewheel)

        var_canvas.pack(side="left", fill="both", expand=True)
        var_scrollbar.pack(side="right", fill="y")

        self.var_list_frame.columnconfigure(1, weight=1)
        self.var_canvas = var_canvas  # Store reference for later use

        paned_window.add(left_panel, minsize=300)

        # Right panel - Preview
        right_panel = ttk.Frame(paned_window)

        preview_frame = ttk.LabelFrame(right_panel, text="Preview (Rendered Prompt)")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=10)

        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state="disabled"
        )
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)

        paned_window.add(right_panel, minsize=300)

    def setup_run_tab(self):
        """Create run tab."""
        run_tab = ttk.Frame(self.notebook)
        self.notebook.add(run_tab, text="Run")

        # Execute frame
        exec_frame = ttk.Frame(run_tab)
        exec_frame.pack(fill="x", padx=10, pady=10)

        self.execute_button = ttk.Button(
            exec_frame,
            text="Run Prompt",
            command=self.execute_prompt
        )
        self.execute_button.pack(side="left", padx=5)

        self.status_label = ttk.Label(exec_frame, text="Ready")
        self.status_label.pack(side="left", padx=10)

        # Response frame
        response_frame = ttk.LabelFrame(run_tab, text="Response")
        response_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.response_text = scrolledtext.ScrolledText(
            response_frame,
            font=("Consolas", 10),
            wrap=tk.WORD,
            state="disabled"
        )
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)

        # History frame
        history_frame = ttk.LabelFrame(run_tab, text="Execution History")
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.history_listbox = tk.Listbox(history_frame, height=6)
        self.history_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(
            history_frame,
            text="View Details",
            command=self.view_history_details
        ).pack(pady=5)

    def setup_status_bar(self):
        """Create status bar."""
        status_bar = ttk.Frame(self)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="EW", padx=5, pady=2)

        self.save_status_label = ttk.Label(status_bar, text="Saved")
        self.save_status_label.pack(side="left", padx=10)

        self.model_label = ttk.Label(status_bar, text="Model: None")
        self.model_label.pack(side="right", padx=10)

        self.status_bar = status_bar

    def bind_events(self):
        """Bind event handlers."""
        # Task selection
        self.task_listbox.bind("<<ListboxSelect>>", self.on_task_select)

        # Text change events for auto-save and highlight
        self.desc_entry.bind("<KeyRelease>", lambda e: self.schedule_autosave())
        self.system_text.bind("<KeyRelease>", lambda e: self.on_text_change(self.system_text))
        self.user_text.bind("<KeyRelease>", lambda e: self.on_text_change(self.user_text))

        # Keyboard shortcuts
        self.bind("<Control-n>", lambda e: self.create_new_task())
        self.bind("<Control-s>", lambda e: self.save_all())
        self.bind("<F5>", lambda e: self.execute_prompt())

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def on_task_select(self, event):
        """Handle task selection."""
        selection = self.task_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.manager.tasks):
            self.current_task = self.manager.tasks[idx]
            self.rename_entry.delete(0, tk.END)
            self.rename_entry.insert(0, self.current_task.name)

            # Load latest version
            if self.current_task.versions:
                self.current_version = self.current_task.versions[-1]
                self.load_version(self.current_version)
                self.refresh_version_buttons()
                self.refresh_history()

    def on_text_change(self, text_widget):
        """Handle text change - autosave and highlight."""
        self.schedule_autosave()
        self.highlight_placeholders(text_widget)

    def highlight_placeholders(self, text_widget):
        """Highlight {{ placeholder }} patterns in text widget."""
        # Remove existing tags
        text_widget.tag_remove("placeholder", "1.0", tk.END)

        # Get current text
        content = text_widget.get("1.0", tk.END)

        # Find all {{ }} patterns
        pattern = r'\{\{[^}]+\}\}'

        for match in re.finditer(pattern, content):
            start_idx = match.start()
            end_idx = match.end()

            # Convert string index to Tkinter text index
            start_line = content[:start_idx].count('\n') + 1
            start_col = start_idx - content[:start_idx].rfind('\n') - 1

            end_line = content[:end_idx].count('\n') + 1
            end_col = end_idx - content[:end_idx].rfind('\n') - 1

            start_pos = f"{start_line}.{start_col}"
            end_pos = f"{end_line}.{end_col}"

            # Apply tag
            text_widget.tag_add("placeholder", start_pos, end_pos)

    def schedule_autosave(self):
        """Schedule auto-save after delay."""
        if self.autosave_timer:
            self.after_cancel(self.autosave_timer)

        self.save_status_label.config(text="Editing...")
        self.autosave_timer = self.after(2000, self.autosave)

    def autosave(self):
        """Auto-save current version."""
        if not self.current_task or not self.current_version:
            return

        try:
            self.current_version.description = self.desc_entry.get()
            self.current_version.system_prompt = self.system_text.get("1.0", tk.END).strip()
            self.current_version.user_prompt = self.user_text.get("1.0", tk.END).strip()
            self.current_task.modified_at = datetime.now().isoformat()

            self.manager.save_tasks()
            self.save_status_label.config(text="Saved")

            # Update variables
            self.refresh_variables()
        except Exception as e:
            self.save_status_label.config(text=f"Error: {str(e)}")

    # ========================================================================
    # Task Management
    # ========================================================================

    def refresh_task_list(self):
        """Refresh the task listbox."""
        self.task_listbox.delete(0, tk.END)
        for task in self.manager.tasks:
            self.task_listbox.insert(tk.END, task.name)

    def create_new_task(self):
        """Create a new task."""
        name = simpledialog.askstring("New Task", "Enter task name:")
        if name and name.strip():
            try:
                task = self.manager.create_task(name.strip())
                self.refresh_task_list()
                # Select the new task
                idx = self.manager.tasks.index(task)
                self.task_listbox.selection_clear(0, tk.END)
                self.task_listbox.selection_set(idx)
                self.task_listbox.event_generate("<<ListboxSelect>>")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create task: {str(e)}")

    def delete_selected_task(self):
        """Delete the selected task."""
        if not self.current_task:
            messagebox.showwarning("Warning", "No task selected")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete task '{self.current_task.name}'? This will remove all versions and results."
        )

        if confirm:
            try:
                self.manager.delete_task(self.current_task)
                self.current_task = None
                self.current_version = None
                self.refresh_task_list()
                self.clear_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {str(e)}")

    def rename_selected_task(self):
        """Rename the selected task."""
        if not self.current_task:
            messagebox.showwarning("Warning", "No task selected")
            return

        new_name = self.rename_entry.get().strip()
        if not new_name:
            messagebox.showwarning("Warning", "Task name cannot be empty")
            return

        try:
            self.manager.rename_task(self.current_task, new_name)
            self.refresh_task_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to rename task: {str(e)}")

    # ========================================================================
    # Version Management
    # ========================================================================

    def refresh_version_buttons(self):
        """Refresh version timeline buttons."""
        # Clear existing buttons
        for widget in self.version_button_frame.winfo_children():
            widget.destroy()

        if not self.current_task:
            return

        # Create button for each version
        for idx, version in enumerate(self.current_task.versions):
            is_current = version == self.current_version
            btn = ttk.Button(
                self.version_button_frame,
                text=f"v{idx+1}",
                width=5,
                command=lambda v=version: self.load_version(v)
            )
            btn.pack(side=tk.LEFT, padx=2)

            # Highlight current version
            if is_current:
                btn.state(['pressed'])

    def create_new_version(self):
        """Create a new version."""
        if not self.current_task:
            messagebox.showwarning("Warning", "No task selected")
            return

        description = simpledialog.askstring(
            "New Version",
            "Enter version description (optional):"
        )

        try:
            version = self.manager.create_version(
                self.current_task,
                description or ""
            )
            self.current_version = version
            self.refresh_version_buttons()
            self.load_version(version)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create version: {str(e)}")

    def load_version(self, version: Version):
        """Load a version into the editor."""
        self.current_version = version

        # Load content
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, version.description)

        self.system_text.delete("1.0", tk.END)
        self.system_text.insert("1.0", version.system_prompt)

        self.user_text.delete("1.0", tk.END)
        self.user_text.insert("1.0", version.user_prompt)

        # Apply highlighting to loaded content
        self.highlight_placeholders(self.system_text)
        self.highlight_placeholders(self.user_text)

        # Refresh variables and history
        self.refresh_variables()
        self.refresh_history()
        self.refresh_version_buttons()

    # ========================================================================
    # Variables Management
    # ========================================================================

    def refresh_variables(self):
        """Refresh variable list and preview."""
        if not self.current_task or not self.current_version:
            return

        # Extract variables from ALL versions in this task (shared across task)
        all_variables = set()
        current_variables = set()
        variable_to_versions = {}  # Track which versions use which variables

        # Get variables from current version
        system_prompt = self.system_text.get("1.0", tk.END).strip()
        user_prompt = self.user_text.get("1.0", tk.END).strip()
        current_variables = set(self.manager.extract_variables(system_prompt + " " + user_prompt))

        # Get variables from all versions in the task and track which versions use them
        for version in self.current_task.versions:
            version_vars = self.manager.extract_variables(
                version.system_prompt + " " + version.user_prompt
            )
            all_variables.update(version_vars)

            # Track which versions use this variable
            for var in version_vars:
                if var not in variable_to_versions:
                    variable_to_versions[var] = []
                variable_to_versions[var].append(version.version_id)

        # Clear existing entries
        for widget in self.var_list_frame.winfo_children():
            widget.destroy()

        if not all_variables:
            ttk.Label(
                self.var_list_frame,
                text="No variables found in any version of this task"
            ).grid(row=0, column=0, columnspan=2, pady=20)
            return

        # Create text area for each variable (shared across all versions)
        row = 0
        for var_name in sorted(all_variables):
            # Indicate if variable is used in current version
            is_current = var_name in current_variables

            # Build label text with version info
            if is_current:
                label_text = f"{{{{ {var_name} }}}}"
            else:
                # Show which versions use this variable
                versions_using = variable_to_versions.get(var_name, [])
                versions_str = ", ".join(versions_using)
                label_text = f"{{{{ {var_name} }}}} ({versions_str})"

            label = ttk.Label(
                self.var_list_frame,
                text=label_text,
                font=("Arial", 10, "bold" if is_current else "normal"),
                foreground="black" if is_current else "gray"
            )
            label.grid(row=row, column=0, sticky="NE", padx=5, pady=3)

            # Use ScrolledText for multi-line variable values
            var_text = scrolledtext.ScrolledText(
                self.var_list_frame,
                height=3,
                width=50,
                font=("Consolas", 9),
                wrap=tk.WORD
            )
            var_text.grid(row=row, column=1, sticky="EW", padx=5, pady=3)

            # Load existing value from task-level variables
            if var_name in self.current_task.variables:
                var_text.insert("1.0", self.current_task.variables[var_name])

            # Save on change (saves to task level, shared by all versions)
            var_text.bind(
                "<FocusOut>",
                lambda e, v=var_name: self.save_variable(v, e.widget.get("1.0", tk.END).strip())
            )
            var_text.bind(
                "<KeyRelease>",
                lambda e: self.update_preview()
            )

            row += 1

        # Update canvas scroll region
        self.var_list_frame.update_idletasks()
        self.var_canvas.configure(scrollregion=self.var_canvas.bbox("all"))

        self.update_preview()

    def save_variable(self, var_name: str, value: str):
        """Save variable value."""
        if not self.current_task:
            return

        self.current_task.variables[var_name] = value
        self.current_task.modified_at = datetime.now().isoformat()
        self.manager.save_tasks()
        self.update_preview()

    def update_preview(self):
        """Update preview with rendered prompt."""
        if not self.current_task or not self.current_version:
            return

        try:
            system_prompt = self.manager.render_prompt(
                self.current_version.system_prompt,
                self.current_task.variables
            )
            user_prompt = self.manager.render_prompt(
                self.current_version.user_prompt,
                self.current_task.variables
            )

            preview = f"System: {system_prompt}\n\nUser: {user_prompt}"

            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview)
            self.preview_text.config(state="disabled")
        except Exception:
            pass

    # ========================================================================
    # LLM Execution
    # ========================================================================

    def execute_prompt(self):
        """Execute the current prompt."""
        if not self.current_task or not self.current_version:
            messagebox.showwarning("Warning", "No task or version selected")
            return

        endpoint = self.manager.get_active_endpoint()
        if not endpoint:
            messagebox.showwarning(
                "Warning",
                "No active endpoint configured. Please configure an endpoint in Settings."
            )
            return

        # Update UI state
        self.execute_button.config(state="disabled", text="Running...")
        self.status_label.config(text="Executing...")

        # Run in thread
        def run():
            try:
                # Render prompts
                system_prompt = self.manager.render_prompt(
                    self.current_version.system_prompt,
                    self.current_task.variables
                )
                user_prompt = self.manager.render_prompt(
                    self.current_version.user_prompt,
                    self.current_task.variables
                )

                # Execute
                response = self.manager.execute_llm(system_prompt, user_prompt, endpoint)

                # Save result
                self.manager.save_result(
                    self.current_task,
                    self.current_version,
                    self.current_task.variables.copy(),
                    user_prompt,
                    response,
                    endpoint.model
                )

                # Update UI
                self.after(0, lambda: self.on_execution_success(response))
            except Exception as e:
                self.after(0, lambda: self.on_execution_error(str(e)))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def on_execution_success(self, response: str):
        """Handle successful execution."""
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", tk.END)
        self.response_text.insert("1.0", response)
        self.response_text.config(state="disabled")

        self.execute_button.config(state="normal", text="Run Prompt")
        self.status_label.config(text="Success")

        self.refresh_history()

    def on_execution_error(self, error: str):
        """Handle execution error."""
        messagebox.showerror("Execution Error", error)
        self.execute_button.config(state="normal", text="Run Prompt")
        self.status_label.config(text="Error")

    # ========================================================================
    # History
    # ========================================================================

    def refresh_history(self):
        """Refresh execution history list."""
        self.history_listbox.delete(0, tk.END)

        if not self.current_task or not self.current_version:
            return

        # Filter results for current version
        results = [
            r for r in self.current_task.results
            if r.version_id == self.current_version.version_id
        ]

        # Show latest first
        for result in reversed(results[-50:]):
            timestamp = result.executed_at[:19].replace('T', ' ')
            preview = result.response[:50].replace('\n', ' ')
            self.history_listbox.insert(
                tk.END,
                f"{timestamp} - {result.model} - {preview}..."
            )

    def view_history_details(self):
        """Show details of selected history item."""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No history item selected")
            return

        if not self.current_task or not self.current_version:
            return

        # Get selected result
        results = [
            r for r in self.current_task.results
            if r.version_id == self.current_version.version_id
        ]
        results = list(reversed(results[-50:]))

        idx = selection[0]
        if idx >= len(results):
            return

        result = results[idx]

        # Create detail dialog
        dialog = tk.Toplevel(self)
        dialog.title("Execution Details")
        dialog.geometry("700x600")
        dialog.transient(self)

        # Content
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=("Consolas", 9))
        text.pack(fill="both", expand=True, padx=10, pady=10)

        content = f"""Executed At: {result.executed_at}
Model: {result.model}
Version: {result.version_id}

Input Variables:
{json.dumps(result.inputs, indent=2)}

Rendered Prompt:
{result.rendered_prompt}

Response:
{result.response}
"""
        text.insert("1.0", content)
        text.config(state="disabled")

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)

    # ========================================================================
    # Settings & Utilities
    # ========================================================================

    def open_settings_dialog(self):
        """Open endpoint configuration dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("LLM Endpoint Settings")
        dialog.geometry("600x400")
        dialog.transient(self)

        # Endpoint list
        ttk.Label(dialog, text="Configured Endpoints:", font=("Arial", 10, "bold")).pack(
            pady=5
        )

        endpoint_frame = ttk.Frame(dialog)
        endpoint_frame.pack(fill="both", expand=True, padx=10, pady=5)

        endpoint_listbox = tk.Listbox(endpoint_frame)
        endpoint_listbox.pack(fill="both", expand=True)

        for endpoint in self.manager.endpoints:
            status = "[ACTIVE]" if endpoint.active else ""
            endpoint_listbox.insert(tk.END, f"{status} {endpoint.name} - {endpoint.model}")

        # Add endpoint button
        def add_endpoint():
            AddEndpointDialog(dialog, self)

        ttk.Button(dialog, text="Add Endpoint", command=add_endpoint).pack(pady=5)

        # Update model label
        self.update_model_label()

    def update_model_label(self):
        """Update the model label in status bar."""
        endpoint = self.manager.get_active_endpoint()
        if endpoint:
            self.model_label.config(text=f"Model: {endpoint.model}")
        else:
            self.model_label.config(text="Model: None")

    def save_all(self):
        """Save all data."""
        try:
            if self.current_task and self.current_version:
                self.autosave()
            self.save_status_label.config(text="All saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Prompt Manager v1.0\n\nLLM Prompt Management Application\n\nManage, version, and test your LLM prompts efficiently."
        )

    def clear_ui(self):
        """Clear all UI fields."""
        self.desc_entry.delete(0, tk.END)
        self.system_text.delete("1.0", tk.END)
        self.user_text.delete("1.0", tk.END)
        self.response_text.config(state="normal")
        self.response_text.delete("1.0", tk.END)
        self.response_text.config(state="disabled")
        self.refresh_version_buttons()
        self.refresh_variables()
        self.refresh_history()


class AddEndpointDialog(tk.Toplevel):
    """Dialog for adding an endpoint."""

    def __init__(self, parent, app: PromptManagerApp):
        super().__init__(parent)
        self.app = app
        self.title("Add Endpoint")
        self.geometry("500x300")
        self.transient(parent)

        # Fields
        fields = [
            ("Name:", "name"),
            ("Base URL:", "base_url"),
            ("API Key:", "api_key"),
            ("Model:", "model")
        ]

        self.entries = {}

        for idx, (label, key) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=idx, column=0, sticky="E", padx=10, pady=5)
            entry = ttk.Entry(self, width=40)
            entry.grid(row=idx, column=1, sticky="EW", padx=10, pady=5)
            self.entries[key] = entry

        # Active checkbox
        self.active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self,
            text="Set as active endpoint",
            variable=self.active_var
        ).grid(row=len(fields), column=0, columnspan=2, pady=10)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side="left", padx=5)

        self.columnconfigure(1, weight=1)

    def save(self):
        """Save the endpoint."""
        try:
            name = self.entries["name"].get().strip()
            base_url = self.entries["base_url"].get().strip()
            api_key = self.entries["api_key"].get().strip()
            model = self.entries["model"].get().strip()

            if not all([name, base_url, api_key, model]):
                messagebox.showwarning("Warning", "All fields are required")
                return

            # Deactivate others if this is active
            if self.active_var.get():
                for endpoint in self.app.manager.endpoints:
                    endpoint.active = False

            endpoint = Endpoint(name, base_url, api_key, model, self.active_var.get())
            self.app.manager.endpoints.append(endpoint)
            self.app.manager.save_config()
            self.app.update_model_label()

            messagebox.showinfo("Success", "Endpoint added successfully")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save endpoint: {str(e)}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    app = PromptManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
