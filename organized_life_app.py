import json
import random
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk


APP_TITLE = "Orbit Organizer"
DATA_FILE = Path(__file__).with_name("organized_life_data.json")

COLORS = {
    "bg": "#070b14",
    "bg_2": "#0b1220",
    "panel": "#101827",
    "panel_2": "#151f32",
    "ink": "#edf6ff",
    "muted": "#8ea3b8",
    "accent": "#36f2c5",
    "accent_dark": "#12bfa1",
    "accent_2": "#7c5cff",
    "warning": "#ffd166",
    "danger": "#ff5c7a",
    "line": "#25354d",
    "soft": "#112d35",
    "input": "#0c1424",
    "select": "#1d3352",
}

QUOTES = [
    "Small progress still counts. Start tiny, then keep moving.",
    "Do the next honest thing. Momentum usually follows.",
    "A lazy day can still have one useful win.",
    "You do not need a perfect mood to take a good action.",
    "Make it easier to begin than to avoid.",
    "Future you is quietly cheering for present you.",
    "Ten focused minutes can change the whole direction of a day.",
]


def today_key():
    return date.today().isoformat()


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


class OrganizedLifeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x720")
        self.minsize(960, 620)
        self.configure(bg=COLORS["bg"])

        self.data = self.load_data()
        self.timer_seconds = 25 * 60
        self.timer_minutes = 25
        self.timer_running = False
        self.timer_job = None
        self.selected_task_id = None
        self.selected_habit_id = None

        self.setup_styles()
        self.build_layout()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*selectBackground", COLORS["select"])
        self.option_add("*selectForeground", COLORS["ink"])

        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"], relief="flat", borderwidth=0)
        style.configure("Tool.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["ink"], font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["ink"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 24))
        style.configure("Metric.TLabel", background=COLORS["panel"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 28))

        style.configure(
            "TButton",
            background=COLORS["panel_2"],
            foreground=COLORS["ink"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["panel_2"],
            darkcolor=COLORS["panel_2"],
            focusthickness=0,
            focuscolor=COLORS["panel_2"],
            font=("Segoe UI Semibold", 10),
            padding=(14, 8),
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("active", COLORS["select"]), ("pressed", COLORS["soft"])],
            foreground=[("disabled", COLORS["muted"])],
            bordercolor=[("active", COLORS["accent"])],
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="#001b18",
            bordercolor=COLORS["accent"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLORS["accent_dark"]), ("pressed", COLORS["accent_dark"])],
            foreground=[("active", "#001b18")],
        )

        style.configure(
            "TEntry",
            fieldbackground=COLORS["input"],
            background=COLORS["input"],
            foreground=COLORS["ink"],
            insertcolor=COLORS["accent"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            padding=(10, 7),
            relief="flat",
        )
        style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["input"],
            background=COLORS["input"],
            foreground=COLORS["ink"],
            arrowcolor=COLORS["accent"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            padding=(8, 6),
            relief="flat",
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["input"])],
            foreground=[("readonly", COLORS["ink"])],
            bordercolor=[("focus", COLORS["accent"])],
        )
        style.configure(
            "Treeview",
            background=COLORS["panel"],
            foreground=COLORS["ink"],
            fieldbackground=COLORS["panel"],
            bordercolor=COLORS["panel"],
            lightcolor=COLORS["panel"],
            darkcolor=COLORS["panel"],
            font=("Segoe UI", 10),
            rowheight=32,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["select"])],
            foreground=[("selected", COLORS["ink"])],
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel_2"],
            foreground=COLORS["accent"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["panel_2"],
            darkcolor=COLORS["panel_2"],
            font=("Segoe UI Semibold", 10),
            padding=(8, 8),
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", COLORS["select"])])
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(0, 8, 0, 0))
        style.configure(
            "TNotebook.Tab",
            background=COLORS["panel"],
            foreground=COLORS["muted"],
            bordercolor=COLORS["bg"],
            lightcolor=COLORS["panel"],
            darkcolor=COLORS["panel"],
            padding=(22, 10),
            font=("Segoe UI Semibold", 10),
            relief="flat",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["accent_2"]), ("active", COLORS["select"])],
            foreground=[("selected", COLORS["ink"]), ("active", COLORS["ink"])],
        )
        style.configure("TSeparator", background=COLORS["line"])

    def build_layout(self):
        header = ttk.Frame(self, padding=(22, 18, 22, 8))
        header.pack(fill="x")

        title_area = ttk.Frame(header)
        title_area.pack(side="left", fill="x", expand=True)
        ttk.Label(title_area, text="Orbit Organizer", style="Title.TLabel").pack(anchor="w")
        self.quote_label = ttk.Label(title_area, text="", foreground=COLORS["muted"], background=COLORS["bg"], font=("Segoe UI", 10))
        self.quote_label.pack(anchor="w", pady=(4, 0))

        ttk.Button(header, text="New Motivation", command=self.pick_quote).pack(side="right", ipadx=4)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=22, pady=(0, 22))

        self.dashboard_tab = ttk.Frame(self.notebook)
        self.tasks_tab = ttk.Frame(self.notebook)
        self.habits_tab = ttk.Frame(self.notebook)
        self.focus_tab = ttk.Frame(self.notebook)
        self.notes_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Today")
        self.notebook.add(self.tasks_tab, text="Tasks")
        self.notebook.add(self.habits_tab, text="Habits")
        self.notebook.add(self.focus_tab, text="Focus")
        self.notebook.add(self.notes_tab, text="Notes")

        self.build_dashboard()
        self.build_tasks()
        self.build_habits()
        self.build_focus()
        self.build_notes()

    def panel(self, parent, padding=14):
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=padding)
        frame.configure(borderwidth=1, relief="solid")
        return frame

    def build_dashboard(self):
        container = ttk.Frame(self.dashboard_tab, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure((0, 1, 2), weight=1)
        container.rowconfigure(1, weight=1)

        self.task_metric = self.metric_card(container, "Open tasks", "0", 0)
        self.habit_metric = self.metric_card(container, "Habits done today", "0", 1)
        self.focus_metric = self.metric_card(container, "Focus minutes today", "0", 2)

        left = self.panel(container)
        left.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=(0, 10), pady=(12, 0))
        ttk.Label(left, text="Mission Queue", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.today_tree = ttk.Treeview(left, columns=("task", "priority", "due"), show="headings", height=11)
        self.today_tree.heading("task", text="Task")
        self.today_tree.heading("priority", text="Priority")
        self.today_tree.heading("due", text="Due")
        self.today_tree.column("task", width=360)
        self.today_tree.column("priority", width=120, anchor="center")
        self.today_tree.column("due", width=120, anchor="center")
        self.today_tree.tag_configure("high", foreground=COLORS["danger"])
        self.today_tree.tag_configure("medium", foreground=COLORS["warning"])
        self.today_tree.tag_configure("low", foreground=COLORS["accent"])
        self.today_tree.tag_configure("overdue", foreground=COLORS["danger"])
        self.today_tree.pack(fill="both", expand=True, pady=(10, 0))

        right = self.panel(container)
        right.grid(row=1, column=2, sticky="nsew", pady=(12, 0))
        ttk.Label(right, text="Quick Capture", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.quick_task_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.quick_task_var).pack(fill="x", pady=(10, 8))
        ttk.Button(right, text="Add Task", style="Accent.TButton", command=self.quick_add_task).pack(fill="x")
        ttk.Separator(right).pack(fill="x", pady=16)
        ttk.Label(right, text="One Win For Today", style="Panel.TLabel", font=("Segoe UI Semibold", 12)).pack(anchor="w")
        self.win_var = tk.StringVar(value=self.data.get("today_win", {}).get(today_key(), ""))
        win_entry = ttk.Entry(right, textvariable=self.win_var)
        win_entry.pack(fill="x", pady=(10, 8))
        ttk.Button(right, text="Save Today's Win", command=self.save_today_win).pack(fill="x")
        self.win_status = ttk.Label(right, text="", style="Muted.TLabel")
        self.win_status.pack(anchor="w", pady=(8, 0))

    def metric_card(self, parent, label, value, column):
        frame = self.panel(parent, padding=16)
        frame.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0 if column == 2 else 8))
        value_label = ttk.Label(frame, text=value, style="Metric.TLabel")
        value_label.pack(anchor="w")
        ttk.Label(frame, text=label, style="Muted.TLabel").pack(anchor="w", pady=(2, 0))
        return value_label

    def build_tasks(self):
        container = ttk.Frame(self.tasks_tab, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        list_panel = self.panel(container)
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(list_panel, text="Task Console", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.task_tree = ttk.Treeview(
            list_panel,
            columns=("status", "priority", "due", "created"),
            show="tree headings",
            height=15,
        )
        self.task_tree.heading("#0", text="Task")
        self.task_tree.heading("status", text="Status")
        self.task_tree.heading("priority", text="Priority")
        self.task_tree.heading("due", text="Due")
        self.task_tree.heading("created", text="Created")
        self.task_tree.column("#0", width=360)
        self.task_tree.column("status", width=90, anchor="center")
        self.task_tree.column("priority", width=90, anchor="center")
        self.task_tree.column("due", width=110, anchor="center")
        self.task_tree.column("created", width=110, anchor="center")
        self.task_tree.tag_configure("done", foreground=COLORS["muted"])
        self.task_tree.tag_configure("high", foreground=COLORS["danger"])
        self.task_tree.tag_configure("medium", foreground=COLORS["warning"])
        self.task_tree.tag_configure("low", foreground=COLORS["accent"])
        self.task_tree.pack(fill="both", expand=True, pady=(10, 8))
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)

        task_buttons = ttk.Frame(list_panel, style="Panel.TFrame")
        task_buttons.pack(fill="x")
        ttk.Button(task_buttons, text="Mark Done", command=self.mark_task_done).pack(side="left", padx=(0, 8))
        ttk.Button(task_buttons, text="Reopen", command=self.reopen_task).pack(side="left", padx=(0, 8))
        ttk.Button(task_buttons, text="Delete", command=self.delete_task).pack(side="left")

        form = self.panel(container)
        form.grid(row=0, column=1, sticky="nsew")
        ttk.Label(form, text="Add / Edit Task", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.task_title_var = tk.StringVar()
        self.task_priority_var = tk.StringVar(value="Medium")
        self.task_due_var = tk.StringVar(value="")
        self.task_notes_var = tk.StringVar(value="")
        self.form_row(form, "Task", ttk.Entry(form, textvariable=self.task_title_var))
        self.form_row(form, "Priority", ttk.Combobox(form, textvariable=self.task_priority_var, values=("High", "Medium", "Low"), state="readonly"))
        self.form_row(form, "Due date", ttk.Entry(form, textvariable=self.task_due_var))
        ttk.Label(form, text="Use YYYY-MM-DD for due date", style="Muted.TLabel").pack(anchor="w", pady=(0, 10))
        self.form_row(form, "Notes", ttk.Entry(form, textvariable=self.task_notes_var))
        ttk.Button(form, text="Save Task", style="Accent.TButton", command=self.save_task).pack(fill="x", pady=(12, 8))
        ttk.Button(form, text="Clear Form", command=self.clear_task_form).pack(fill="x")

    def form_row(self, parent, label, widget):
        ttk.Label(parent, text=label, style="Panel.TLabel").pack(anchor="w", pady=(12, 4))
        widget.pack(fill="x")

    def build_habits(self):
        container = ttk.Frame(self.habits_tab, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        list_panel = self.panel(container)
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(list_panel, text="Habit Signals", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.habit_tree = ttk.Treeview(list_panel, columns=("today", "streak"), show="tree headings", height=15)
        self.habit_tree.heading("#0", text="Habit")
        self.habit_tree.heading("today", text="Today")
        self.habit_tree.heading("streak", text="Streak")
        self.habit_tree.column("#0", width=360)
        self.habit_tree.column("today", width=100, anchor="center")
        self.habit_tree.column("streak", width=100, anchor="center")
        self.habit_tree.tag_configure("checked", foreground=COLORS["accent"])
        self.habit_tree.tag_configure("unchecked", foreground=COLORS["muted"])
        self.habit_tree.pack(fill="both", expand=True, pady=(10, 8))
        self.habit_tree.bind("<<TreeviewSelect>>", self.on_habit_select)

        habit_buttons = ttk.Frame(list_panel, style="Panel.TFrame")
        habit_buttons.pack(fill="x")
        ttk.Button(habit_buttons, text="Check Today", command=self.check_habit_today).pack(side="left", padx=(0, 8))
        ttk.Button(habit_buttons, text="Uncheck Today", command=self.uncheck_habit_today).pack(side="left", padx=(0, 8))
        ttk.Button(habit_buttons, text="Delete", command=self.delete_habit).pack(side="left")

        form = self.panel(container)
        form.grid(row=0, column=1, sticky="nsew")
        ttk.Label(form, text="Add Habit", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        self.habit_name_var = tk.StringVar()
        self.form_row(form, "Habit name", ttk.Entry(form, textvariable=self.habit_name_var))
        ttk.Button(form, text="Save Habit", style="Accent.TButton", command=self.save_habit).pack(fill="x", pady=(12, 8))
        ttk.Button(form, text="Clear", command=self.clear_habit_form).pack(fill="x")

    def build_focus(self):
        container = ttk.Frame(self.focus_tab, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        panel = self.panel(container, padding=28)
        panel.grid(row=0, column=0, sticky="nsew")
        ttk.Label(panel, text="Focus Reactor", style="Panel.TLabel", font=("Segoe UI Semibold", 16)).pack(anchor="center")
        self.timer_label = ttk.Label(panel, text="25:00", style="Metric.TLabel", font=("Segoe UI Semibold", 72))
        self.timer_label.pack(pady=(30, 12))
        self.focus_status = ttk.Label(panel, text="Pick one task, then give it 25 minutes.", style="Muted.TLabel")
        self.focus_status.pack()

        controls = ttk.Frame(panel, style="Panel.TFrame")
        controls.pack(pady=24)
        ttk.Button(controls, text="Start", style="Accent.TButton", command=self.start_timer).pack(side="left", padx=6)
        ttk.Button(controls, text="Pause", command=self.pause_timer).pack(side="left", padx=6)
        ttk.Button(controls, text="Reset 25", command=lambda: self.reset_timer(25)).pack(side="left", padx=6)
        ttk.Button(controls, text="Reset 5", command=lambda: self.reset_timer(5)).pack(side="left", padx=6)

    def build_notes(self):
        container = ttk.Frame(self.notes_tab, padding=12)
        container.pack(fill="both", expand=True)
        panel = self.panel(container)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Memory Cache", style="Panel.TLabel", font=("Segoe UI Semibold", 13)).pack(anchor="w")
        ttk.Label(panel, text="Drop loose thoughts here so they stop stealing your attention.", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))
        self.notes_text = tk.Text(
            panel,
            wrap="word",
            height=18,
            bg=COLORS["input"],
            fg=COLORS["ink"],
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["select"],
            selectforeground=COLORS["ink"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
            padx=14,
            pady=12,
            font=("Segoe UI", 11),
        )
        self.notes_text.pack(fill="both", expand=True)
        self.notes_text.insert("1.0", self.data.get("notes", ""))
        ttk.Button(panel, text="Save Notes", style="Accent.TButton", command=self.save_notes).pack(anchor="e", pady=(10, 0))

    def load_data(self):
        default = {
            "tasks": [],
            "habits": [],
            "notes": "",
            "today_win": {},
            "focus_minutes": {},
        }
        if not DATA_FILE.exists():
            return default
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                saved = json.load(file)
            default.update(saved)
            return default
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning("Data issue", "Could not read saved data. Starting fresh for now.")
            return default

    def save_data(self):
        self.data["notes"] = self.notes_text.get("1.0", "end-1c") if hasattr(self, "notes_text") else self.data.get("notes", "")
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)

    def next_id(self, collection):
        ids = [item.get("id", 0) for item in self.data.get(collection, [])]
        return max(ids, default=0) + 1

    def refresh_all(self):
        self.pick_quote()
        self.refresh_tasks()
        self.refresh_habits()
        self.refresh_dashboard()
        self.update_timer_label()

    def pick_quote(self):
        self.quote_label.configure(text=random.choice(QUOTES))

    def refresh_dashboard(self):
        open_tasks = [task for task in self.data["tasks"] if not task.get("done")]
        habits_done = sum(1 for habit in self.data["habits"] if today_key() in habit.get("done_dates", []))
        focus_minutes = self.data["focus_minutes"].get(today_key(), 0)
        self.task_metric.configure(text=str(len(open_tasks)))
        self.habit_metric.configure(text=f"{habits_done}/{len(self.data['habits'])}")
        self.focus_metric.configure(text=str(focus_minutes))

        self.today_tree.delete(*self.today_tree.get_children())
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(
            open_tasks,
            key=lambda task: (
                priority_order.get(task.get("priority"), 3),
                parse_date(task.get("due")) or date.max,
                task.get("created", ""),
            ),
        )
        for task in sorted_tasks[:12]:
            due = task.get("due", "")
            label = task["title"]
            tags = [task.get("priority", "").lower()]
            if due and parse_date(due) and parse_date(due) < date.today():
                label = f"{label}  (overdue)"
                tags.append("overdue")
            self.today_tree.insert("", "end", values=(label, task.get("priority", ""), due), tags=tags)

    def refresh_tasks(self):
        self.task_tree.delete(*self.task_tree.get_children())
        for task in self.data["tasks"]:
            status = "Done" if task.get("done") else "Open"
            tags = ["done"] if task.get("done") else [task.get("priority", "").lower()]
            self.task_tree.insert(
                "",
                "end",
                iid=str(task["id"]),
                text=task["title"],
                values=(status, task.get("priority", ""), task.get("due", ""), task.get("created", "")),
                tags=tags,
            )

    def refresh_habits(self):
        self.habit_tree.delete(*self.habit_tree.get_children())
        for habit in self.data["habits"]:
            done_dates = set(habit.get("done_dates", []))
            today = "Yes" if today_key() in done_dates else "No"
            tag = "checked" if today == "Yes" else "unchecked"
            self.habit_tree.insert("", "end", iid=str(habit["id"]), text=habit["name"], values=(today, self.habit_streak(habit)), tags=(tag,))

    def quick_add_task(self):
        title = self.quick_task_var.get().strip()
        if not title:
            return
        self.data["tasks"].append(
            {
                "id": self.next_id("tasks"),
                "title": title,
                "priority": "Medium",
                "due": today_key(),
                "notes": "",
                "created": today_key(),
                "done": False,
            }
        )
        self.quick_task_var.set("")
        self.save_data()
        self.refresh_tasks()
        self.refresh_dashboard()

    def on_task_select(self, _event=None):
        selection = self.task_tree.selection()
        if not selection:
            return
        self.selected_task_id = int(selection[0])
        task = self.find_item("tasks", self.selected_task_id)
        if task:
            self.task_title_var.set(task.get("title", ""))
            self.task_priority_var.set(task.get("priority", "Medium"))
            self.task_due_var.set(task.get("due", ""))
            self.task_notes_var.set(task.get("notes", ""))

    def save_task(self):
        title = self.task_title_var.get().strip()
        due = self.task_due_var.get().strip()
        if not title:
            messagebox.showinfo("Missing task", "Give the task a name first.")
            return
        if due and not parse_date(due):
            messagebox.showinfo("Date format", "Please use YYYY-MM-DD for due dates.")
            return
        task = self.find_item("tasks", self.selected_task_id) if self.selected_task_id else None
        if not task:
            task = {"id": self.next_id("tasks"), "created": today_key(), "done": False}
            self.data["tasks"].append(task)
        task.update(
            {
                "title": title,
                "priority": self.task_priority_var.get(),
                "due": due,
                "notes": self.task_notes_var.get().strip(),
            }
        )
        self.save_data()
        self.clear_task_form()
        self.refresh_tasks()
        self.refresh_dashboard()

    def clear_task_form(self):
        self.selected_task_id = None
        self.task_title_var.set("")
        self.task_priority_var.set("Medium")
        self.task_due_var.set("")
        self.task_notes_var.set("")
        self.task_tree.selection_remove(self.task_tree.selection())

    def mark_task_done(self):
        task = self.selected_task()
        if task:
            task["done"] = True
            task["completed"] = today_key()
            self.save_data()
            self.refresh_tasks()
            self.refresh_dashboard()

    def reopen_task(self):
        task = self.selected_task()
        if task:
            task["done"] = False
            task.pop("completed", None)
            self.save_data()
            self.refresh_tasks()
            self.refresh_dashboard()

    def delete_task(self):
        task = self.selected_task()
        if not task:
            return
        if messagebox.askyesno("Delete task", f"Delete '{task['title']}'?"):
            self.data["tasks"] = [item for item in self.data["tasks"] if item["id"] != task["id"]]
            self.save_data()
            self.clear_task_form()
            self.refresh_tasks()
            self.refresh_dashboard()

    def selected_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showinfo("No task selected", "Select a task first.")
            return None
        return self.find_item("tasks", int(selection[0]))

    def on_habit_select(self, _event=None):
        selection = self.habit_tree.selection()
        if not selection:
            return
        self.selected_habit_id = int(selection[0])
        habit = self.find_item("habits", self.selected_habit_id)
        if habit:
            self.habit_name_var.set(habit.get("name", ""))

    def save_habit(self):
        name = self.habit_name_var.get().strip()
        if not name:
            messagebox.showinfo("Missing habit", "Give the habit a name first.")
            return
        habit = self.find_item("habits", self.selected_habit_id) if self.selected_habit_id else None
        if not habit:
            habit = {"id": self.next_id("habits"), "name": name, "done_dates": []}
            self.data["habits"].append(habit)
        else:
            habit["name"] = name
        self.save_data()
        self.clear_habit_form()
        self.refresh_habits()
        self.refresh_dashboard()

    def clear_habit_form(self):
        self.selected_habit_id = None
        self.habit_name_var.set("")
        self.habit_tree.selection_remove(self.habit_tree.selection())

    def check_habit_today(self):
        habit = self.selected_habit()
        if habit:
            done_dates = set(habit.get("done_dates", []))
            done_dates.add(today_key())
            habit["done_dates"] = sorted(done_dates)
            self.save_data()
            self.refresh_habits()
            self.refresh_dashboard()

    def uncheck_habit_today(self):
        habit = self.selected_habit()
        if habit:
            habit["done_dates"] = [item for item in habit.get("done_dates", []) if item != today_key()]
            self.save_data()
            self.refresh_habits()
            self.refresh_dashboard()

    def delete_habit(self):
        habit = self.selected_habit()
        if not habit:
            return
        if messagebox.askyesno("Delete habit", f"Delete '{habit['name']}'?"):
            self.data["habits"] = [item for item in self.data["habits"] if item["id"] != habit["id"]]
            self.save_data()
            self.clear_habit_form()
            self.refresh_habits()
            self.refresh_dashboard()

    def selected_habit(self):
        selection = self.habit_tree.selection()
        if not selection:
            messagebox.showinfo("No habit selected", "Select a habit first.")
            return None
        return self.find_item("habits", int(selection[0]))

    def habit_streak(self, habit):
        done_dates = {parse_date(item) for item in habit.get("done_dates", [])}
        done_dates.discard(None)
        streak = 0
        cursor = date.today()
        while cursor in done_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def start_timer(self):
        if self.timer_running:
            return
        self.timer_running = True
        self.focus_status.configure(text="Focus mode is running. Keep the next action small.")
        self.tick_timer()

    def pause_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.focus_status.configure(text="Paused. Restart when you are ready.")

    def reset_timer(self, minutes):
        self.pause_timer()
        self.timer_minutes = minutes
        self.timer_seconds = minutes * 60
        self.update_timer_label()
        self.focus_status.configure(text=f"{minutes} minute timer ready.")

    def tick_timer(self):
        self.update_timer_label()
        if not self.timer_running:
            return
        if self.timer_seconds <= 0:
            self.timer_running = False
            if self.timer_minutes >= 25:
                self.add_focus_minutes(self.timer_minutes)
                self.focus_status.configure(text="Nice. One focus block complete.")
                messagebox.showinfo("Focus complete", "Great job. Take a short break.")
            else:
                self.focus_status.configure(text="Break complete. Ready for the next small win.")
                messagebox.showinfo("Break complete", "Break done. Ready when you are.")
            self.reset_timer(25)
            return
        self.timer_seconds -= 1
        self.timer_job = self.after(1000, self.tick_timer)

    def update_timer_label(self):
        minutes, seconds = divmod(self.timer_seconds, 60)
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

    def add_focus_minutes(self, minutes):
        focus = self.data.setdefault("focus_minutes", {})
        focus[today_key()] = focus.get(today_key(), 0) + minutes
        self.save_data()
        self.refresh_dashboard()

    def save_today_win(self):
        self.data.setdefault("today_win", {})[today_key()] = self.win_var.get().strip()
        self.save_data()
        self.win_status.configure(text="Saved.")

    def save_notes(self):
        self.save_data()
        messagebox.showinfo("Notes saved", "Your notes are saved.")

    def find_item(self, collection, item_id):
        for item in self.data.get(collection, []):
            if item.get("id") == item_id:
                return item
        return None

    def on_close(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.save_data()
        self.destroy()


if __name__ == "__main__":
    app = OrganizedLifeApp()
    app.mainloop()
