import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
from threading import Thread
from datetime import datetime
from gemini_client import generate_spec
from catalog_client import (
    detect_multiple_automations,
    simulate_execution,
    find_automation_by_id
)


class RPASpecGeneratorApp:
    """Desktop GUI for generating RPA workflow specifications and simulating predefined catalog automations."""

    # -- colour palette & fonts --
    BG           = "#1e1e2e"
    SURFACE      = "#2a2a3d"
    ACCENT       = "#7c3aed"
    ACCENT_HOVER = "#6d28d9"
    TEXT         = "#e2e8f0"
    TEXT_DIM     = "#94a3b8"
    BORDER       = "#3b3b55"
    INPUT_BG     = "#232336"
    FONT_FAMILY  = "Segoe UI"
    FONT_MAIN    = ("Segoe UI", 11)
    FONT_TITLE   = ("Segoe UI", 18, "bold")
    FONT_LABEL   = ("Segoe UI", 11, "bold")
    FONT_MONO    = ("Consolas", 11)
    FONT_BTN     = ("Segoe UI", 11, "bold")

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.check_status_btn = None
        self._configure_window()
        self._build_ui()
        self._update_status_bar()

    # ------------------------------------------------------------------ #
    #  Window setup                                                       #
    # ------------------------------------------------------------------ #
    def _configure_window(self) -> None:
        self.root.title("RPA Workflow Spec Generator")
        self.root.geometry("820x740")
        self.root.minsize(640, 580)
        self.root.configure(bg=self.BG)
        self.root.option_add("*Font", self.FONT_MAIN)

        # Style TTK Notebook to match our dark theme
        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("TNotebook", background=self.BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.SURFACE,
            foreground=self.TEXT,
            padding=[18, 6],
            font=self.FONT_BTN,
            borderwidth=0,
            focuscolor="",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.ACCENT)],
            foreground=[("selected", "#ffffff")],
        )

    # ------------------------------------------------------------------ #
    #  UI construction                                                    #
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        # Main container with padding
        container = tk.Frame(self.root, bg=self.BG, padx=28, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        # ── Title ──
        self.title_label = tk.Label(
            container,
            text="⚙  RPA Workflow Spec Generator",
            font=self.FONT_TITLE,
            fg=self.ACCENT,
            bg=self.BG,
            anchor="w",
        )
        self.title_label.pack(fill=tk.X, pady=(0, 14))

        # ── Notebook Tab Bar ──
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab Frames
        self.tab_spec = tk.Frame(self.notebook, bg=self.BG)
        self.tab_run = tk.Frame(self.notebook, bg=self.BG)

        self.notebook.add(self.tab_spec, text="Spec Generator")
        self.notebook.add(self.tab_run, text="Run Automation")

        # Bind tab changes to dynamically update heading
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Build individual tabs
        self._build_tab_spec()
        self._build_tab_run()

    def _on_tab_changed(self, event) -> None:
        """Updates main window title based on the selected tab index."""
        try:
            selected_tab = self.notebook.index(self.notebook.select())
            if selected_tab == 0:
                self.title_label.configure(text="⚙  RPA Workflow Spec Generator")
            else:
                self.title_label.configure(text="⚙  RPA Workflow Simulator")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  TAB 1: Spec Generator                                             #
    # ------------------------------------------------------------------ #
    def _build_tab_spec(self) -> None:
        tab_container = tk.Frame(self.tab_spec, bg=self.BG, pady=10)
        tab_container.pack(fill=tk.BOTH, expand=True)

        # Input label
        lbl_input = tk.Label(
            tab_container,
            text="Describe your automation:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_input.pack(fill=tk.X, pady=(0, 6))

        # Input text area
        input_frame = tk.Frame(tab_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
        input_frame.pack(fill=tk.X, pady=(0, 12))

        self.input_text = tk.Text(
            input_frame,
            height=5,
            wrap=tk.WORD,
            font=self.FONT_MAIN,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=8,
        )
        self.input_text.pack(fill=tk.X)

        # Generate button
        self.generate_btn = tk.Button(
            tab_container,
            text="✦  Generate Spec",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._on_generate,
        )
        self.generate_btn.pack(anchor="w", pady=(0, 16))
        self.generate_btn.bind("<Enter>", lambda e: self.generate_btn.configure(bg=self.ACCENT_HOVER))
        self.generate_btn.bind("<Leave>", lambda e: self.generate_btn.configure(bg=self.ACCENT))

        # Output label
        lbl_output = tk.Label(
            tab_container,
            text="Generated Specification:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_output.pack(fill=tk.X, pady=(0, 6))

        # Output text area (scrollable)
        output_frame = tk.Frame(tab_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=self.FONT_MONO,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            state=tk.DISABLED,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            tab_container,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            fg=self.TEXT_DIM,
            bg=self.BG,
            anchor="w",
        )
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        # Action buttons row
        btn_row = tk.Frame(tab_container, bg=self.BG)
        btn_row.pack(fill=tk.X)

        self.copy_btn = tk.Button(
            btn_row,
            text="📋  Copy to Clipboard",
            font=self.FONT_BTN,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.BORDER,
            activeforeground=self.TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._copy_to_clipboard,
        )
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.copy_btn.bind("<Enter>", lambda e: self.copy_btn.configure(bg=self.BORDER))
        self.copy_btn.bind("<Leave>", lambda e: self.copy_btn.configure(bg=self.SURFACE))

        self.save_btn = tk.Button(
            btn_row,
            text="💾  Save as .txt",
            font=self.FONT_BTN,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.BORDER,
            activeforeground=self.TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._save_to_file,
        )
        self.save_btn.pack(side=tk.LEFT)
        self.save_btn.bind("<Enter>", lambda e: self.save_btn.configure(bg=self.BORDER))
        self.save_btn.bind("<Leave>", lambda e: self.save_btn.configure(bg=self.SURFACE))

    # ------------------------------------------------------------------ #
    #  TAB 2: Run Automation                                             #
    # ------------------------------------------------------------------ #
    def _build_tab_run(self) -> None:
        tab_container = tk.Frame(self.tab_run, bg=self.BG, pady=10)
        tab_container.pack(fill=tk.BOTH, expand=True)

        # ── STATUS BAR ──
        status_bar = tk.Frame(tab_container, bg=self.SURFACE, bd=1, relief=tk.SOLID, padx=12, pady=6)
        status_bar.pack(fill=tk.X, pady=(0, 10))

        self.status_dot = tk.Label(
            status_bar,
            text="●",
            font=("Segoe UI", 12, "bold"),
            bg=self.SURFACE,
            fg="#f97316",
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 4))

        self.status_text = tk.Label(
            status_bar,
            text="0 workflows loaded from AutomationEdge  •  Last synced: Never",
            font=("Segoe UI", 9),
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.refresh_btn = tk.Button(
            status_bar,
            text="↻ Refresh",
            font=("Segoe UI", 9, "bold"),
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=2,
            command=self._on_refresh,
        )
        self.refresh_btn.pack(side=tk.RIGHT)
        self.refresh_btn.bind("<Enter>", lambda e: self.refresh_btn.configure(bg=self.ACCENT_HOVER))
        self.refresh_btn.bind("<Leave>", lambda e: self.refresh_btn.configure(bg=self.ACCENT))

        # ── SECTION A: Prompt Input ──
        lbl_run_prompt = tk.Label(
            tab_container,
            text="What do you want to automate?",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_run_prompt.pack(fill=tk.X, pady=(0, 6))

        run_input_frame = tk.Frame(tab_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
        run_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.run_prompt_entry = tk.Entry(
            run_input_frame,
            font=self.FONT_MAIN,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            relief=tk.FLAT,
        )
        self.run_prompt_entry.pack(fill=tk.X, ipady=8, padx=10)

        # Find button
        self.find_btn = tk.Button(
            tab_container,
            text="🔍  Find Automation →",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            command=self._on_find_automation,
        )
        self.find_btn.pack(anchor="w", pady=(0, 14))
        self.find_btn.bind("<Enter>", lambda e: self.find_btn.configure(bg=self.ACCENT_HOVER))
        self.find_btn.bind("<Leave>", lambda e: self.find_btn.configure(bg=self.ACCENT))

        # Status label for Run Automation Tab
        self.run_status_var = tk.StringVar(value="")
        self.run_status_label = tk.Label(
            tab_container,
            textvariable=self.run_status_var,
            font=("Segoe UI", 10),
            fg=self.TEXT_DIM,
            bg=self.BG,
            anchor="w",
        )
        self.run_status_label.pack(fill=tk.X, pady=(0, 8))

        # Dynamic Results and Form Container
        self.run_container = tk.Frame(tab_container, bg=self.BG)
        self.run_container.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------ #
    #  Tab 1 Logic                                                      #
    # ------------------------------------------------------------------ #
    def _on_generate(self) -> None:
        """Kick off spec generation in a background thread."""
        user_prompt = self.input_text.get("1.0", tk.END).strip()
        if not user_prompt:
            messagebox.showwarning("Input Required", "Please describe your automation before generating.")
            return

        self.generate_btn.configure(state=tk.DISABLED, text="⏳  Generating…")
        self.status_var.set("Generating specification — please wait…")
        self._set_output("")

        thread = Thread(target=self._run_generation, args=(user_prompt,), daemon=True)
        thread.start()

    def _run_generation(self, user_prompt: str) -> None:
        """Runs in a background thread — calls Gemini and posts result back to UI."""
        result = generate_spec(user_prompt)
        self.root.after(0, self._on_generation_complete, result)

    def _on_generation_complete(self, result: str) -> None:
        """Called on the main thread when generation finishes."""
        self._set_output(result)
        self.generate_btn.configure(state=tk.NORMAL, text="✦  Generate Spec")
        self.status_var.set("✔  Specification generated successfully.")

    def _set_output(self, text: str) -> None:
        """Replace the contents of the output text area."""
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state=tk.DISABLED)

    def _copy_to_clipboard(self) -> None:
        """Copy the output text to the system clipboard."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            self.status_var.set("Nothing to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("✔  Copied to clipboard.")

    def _save_to_file(self) -> None:
        """Open a Save-As dialog and write the output to a .txt file."""
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            self.status_var.set("Nothing to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Specification",
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_var.set(f"✔  Saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save file:\n{e}")

    # ------------------------------------------------------------------ #
    #  Tab 2 Logic                                                      #
    # ------------------------------------------------------------------ #
    def _on_refresh(self) -> None:
        """Triggers sync_mappings(force=True) in a background thread."""
        self.refresh_btn.configure(state=tk.DISABLED, text="⏳ Syncing...")
        
        def run_sync():
            try:
                from sync_manager import sync_mappings
                import catalog_client
                mappings = sync_mappings(force=True)
                catalog_client.initialize(mappings)
            except Exception as e:
                print(f"Error during manual refresh: {e}")
            finally:
                self.root.after(0, self._update_status_bar)
                
        Thread(target=run_sync, daemon=True).start()

    def _update_status_bar(self) -> None:
        """Loads data from cache and updates the top status bar indicators."""
        try:
            from sync_manager import load_cache
            cache = load_cache()
            mappings = cache.get("mappings", [])
            last_synced = cache.get("last_synced")
            
            n = len(mappings)
            if last_synced:
                try:
                    timestamp = last_synced[:19].replace("T", " ")
                except Exception:
                    timestamp = str(last_synced)
            else:
                timestamp = "Never"
                
            dot_color = "#22c55e" if n > 0 else "#f97316"
            self.status_dot.configure(fg=dot_color)
            self.status_text.configure(text=f"{n} workflows loaded from AutomationEdge  •  Last synced: {timestamp}")
        except Exception as e:
            print(f"Error updating status bar: {e}")
        finally:
            self.refresh_btn.configure(state=tk.NORMAL, text="↻ Refresh")

    def _on_find_automation(self) -> None:
        """Starts background thread to detect catalog automation matching prompt."""
        prompt = self.run_prompt_entry.get().strip()
        if not prompt:
            messagebox.showwarning("Input Required", "Please describe what you want to automate.")
            return

        self.find_btn.configure(state=tk.DISABLED, text="⏳  Searching…")
        self.run_status_var.set("Searching automation catalog...")

        # Clear active Check Status button reference if any
        self.check_status_btn = None

        # Reset container
        for widget in self.run_container.winfo_children():
            widget.destroy()

        thread = Thread(target=self._run_detection, args=(prompt,), daemon=True)
        thread.start()

    def _run_detection(self, prompt: str) -> None:
        """Detect matched automation IDs in a background thread."""
        results = detect_multiple_automations(prompt)
        self.root.after(0, self._on_detection_complete, results, prompt)

    def _on_detection_complete(self, results: list, prompt: str) -> None:
        """Callback to main thread once automation search returns."""
        self.find_btn.configure(state=tk.NORMAL, text="🔍  Find Automation →")

        n = len(results)
        if n == 0:
            self.run_status_var.set("No matching automation found.")
            self._build_no_match_ui(prompt)
        elif n == 1:
            self.run_status_var.set(f"✔ Matched catalog entry: {results[0]['id']}")
            self._build_matched_ui(results[0])
        else:
            self.run_status_var.set(f"✔ Found {n} relevant automations.")
            self._build_multi_match_ui(results)

    def _build_no_match_ui(self, prompt: str) -> None:
        """Create visual feedback panel when no match is found (Section E)."""
        frame = tk.Frame(self.run_container, bg=self.BG, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = tk.Label(
            frame,
            text="❌  No matching automation found for your request.\n\nTry rephrasing, or:",
            font=self.FONT_MAIN,
            fg=self.TEXT_DIM,
            bg=self.BG,
            justify=tk.CENTER,
        )
        lbl.pack(pady=(20, 15))

        btn = tk.Button(
            frame,
            text="Generate Spec Instead →",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=8,
            command=lambda: self._go_to_spec_generator(prompt),
        )
        btn.pack()
        btn.bind("<Enter>", lambda e: btn.configure(bg=self.ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=self.ACCENT))

    def _go_to_spec_generator(self, prompt: str) -> None:
        """Switches to Tab 1 and populates input prompt."""
        self.notebook.select(0)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, prompt)

    def _build_multi_match_ui(self, results: list) -> None:
        """Renders Section B dropdown selection when multiple matches are found."""
        dropdown_frame = tk.Frame(self.run_container, bg=self.BG, pady=10)
        dropdown_frame.pack(fill=tk.X)
        
        lbl = tk.Label(
            dropdown_frame,
            text=f"We found {len(results)} relevant automations. Select one:",
            font=self.FONT_MAIN,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl.pack(side=tk.LEFT, padx=(0, 10))
        
        names = [r["name"] for r in results]
        var = tk.StringVar(value=names[0])
        
        opt_frame = tk.Frame(dropdown_frame, bg=self.BORDER, bd=1, relief=tk.SOLID)
        opt_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        opt_menu = tk.OptionMenu(
            opt_frame,
            var,
            *names,
            command=lambda selected_name: self._on_dropdown_selection_changed(selected_name, results)
        )
        opt_menu.config(
            bg=self.INPUT_BG,
            fg=self.TEXT,
            activebackground=self.SURFACE,
            activeforeground=self.TEXT,
            relief=tk.FLAT,
            highlightthickness=0,
            font=self.FONT_MAIN,
        )
        opt_menu["menu"].config(
            bg=self.INPUT_BG,
            fg=self.TEXT,
            activebackground=self.ACCENT,
            activeforeground="#ffffff",
            font=self.FONT_MAIN,
        )
        opt_menu.pack(fill=tk.X, ipady=4)
        
        # Section C container
        self.form_container = tk.Frame(self.run_container, bg=self.BG)
        self.form_container.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Initially build form for first option
        self._build_matched_form_ui(results[0])

    def _on_dropdown_selection_changed(self, selected_name: str, results: list) -> None:
        """Callback to rebuild Section C dynamically when selection updates."""
        for widget in self.form_container.winfo_children():
            widget.destroy()

        self.check_status_btn = None
            
        selected_wf = None
        for r in results:
            if r["name"] == selected_name:
                selected_wf = r
                break
                
        if selected_wf:
            self._build_matched_form_ui(selected_wf)

    def _build_matched_ui(self, workflow: dict) -> None:
        """Entry point for rendering a single match workflow layout directly."""
        self.form_container = tk.Frame(self.run_container, bg=self.BG)
        self.form_container.pack(fill=tk.BOTH, expand=True)
        self._build_matched_form_ui(workflow)

    def _build_matched_form_ui(self, workflow: dict) -> None:
        """Renders Section C dynamic inputs and Section D simulation outputs."""
        main_split = tk.Frame(self.form_container, bg=self.BG)
        main_split.pack(fill=tk.BOTH, expand=True)

        # Left Column Scrollable Container
        left_outer = tk.Frame(main_split, bg=self.BG)
        left_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        canvas = tk.Canvas(left_outer, bg=self.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(left_outer, orient="vertical", command=canvas.yview)
        left_col = tk.Frame(canvas, bg=self.BG)

        left_col.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=left_col, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _configure_canvas(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _configure_canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Right Column
        right_col = tk.Frame(main_split, bg=self.BG)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        # Left Column Card Content (Section C)
        card = tk.Frame(left_col, bg=self.SURFACE, bd=1, relief=tk.SOLID, padx=15, pady=12)
        card.pack(fill=tk.X, pady=(0, 10))

        lbl_name = tk.Label(
            card,
            text=workflow.get("name"),
            font=("Segoe UI", 13, "bold"),
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        lbl_name.pack(fill=tk.X, pady=(0, 3))

        lbl_desc = tk.Label(
            card,
            text=workflow.get("description") or "",
            font=("Segoe UI", 9),
            fg=self.TEXT_DIM,
            bg=self.SURFACE,
            wraplength=350,
            justify=tk.LEFT,
            anchor="w",
        )
        lbl_desc.pack(fill=tk.X, pady=(0, 8))

        lbl_outputs_title = tk.Label(
            card,
            text="This automation will produce:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        lbl_outputs_title.pack(fill=tk.X, pady=(0, 3))

        for out in workflow.get("expected_outputs", []):
            lbl_out = tk.Label(
                card,
                text=f"  • {out}",
                font=("Segoe UI", 9),
                fg=self.TEXT_DIM,
                bg=self.SURFACE,
                anchor="w",
                justify=tk.LEFT,
                wraplength=330,
            )
            lbl_out.pack(fill=tk.X)

        # Thin divider line
        divider = tk.Frame(card, height=1, bg=self.BORDER)
        divider.pack(fill=tk.X, pady=(10, 10))

        # Inputs Form Inside Card
        form_frame = tk.Frame(card, bg=self.SURFACE)
        form_frame.pack(fill=tk.X)

        lbl_inputs_title = tk.Label(
            form_frame,
            text="Required Inputs:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        lbl_inputs_title.pack(fill=tk.X, pady=(0, 6))

        grid_frame = tk.Frame(form_frame, bg=self.SURFACE)
        grid_frame.pack(fill=tk.X, pady=(0, 10))
        grid_frame.columnconfigure(0, weight=1, uniform="group1")
        grid_frame.columnconfigure(1, weight=1, uniform="group1")

        self.run_inputs = {}

        for idx, inp in enumerate(workflow.get("required_inputs", [])):
            field_name = inp["field"]
            field_label = inp["label"]
            field_type = inp["type"]
            placeholder = inp.get("placeholder", "")

            # Mark optional fields with "(optional)" in label
            if inp.get("optional", False):
                field_label = f"{field_label} (optional)"

            row = idx // 2
            col = idx % 2

            field_container = tk.Frame(grid_frame, bg=self.SURFACE, pady=4, padx=5)
            
            is_last = (idx == len(workflow.get("required_inputs", [])) - 1)
            is_odd = (len(workflow.get("required_inputs", [])) % 2 == 1)
            if is_last and is_odd:
                field_container.grid(row=row, column=0, columnspan=2, sticky="ew")
            else:
                field_container.grid(row=row, column=col, sticky="ew")

            lbl_f = tk.Label(
                field_container,
                text=field_label,
                font=("Segoe UI", 9, "bold"),
                fg=self.TEXT_DIM,
                bg=self.SURFACE,
                anchor="w",
            )
            lbl_f.pack(fill=tk.X, pady=(0, 2))

            if field_type == "dropdown":
                options = inp.get("options", [])
                var = tk.StringVar(value=options[0] if options else "Select Options")
                self.run_inputs[field_name] = var

                opt_frame = tk.Frame(field_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
                opt_frame.pack(fill=tk.X)

                opt_menu = tk.OptionMenu(opt_frame, var, *options)
                opt_menu.config(
                    bg=self.INPUT_BG,
                    fg=self.TEXT,
                    activebackground=self.SURFACE,
                    activeforeground=self.TEXT,
                    relief=tk.FLAT,
                    highlightthickness=0,
                    font=self.FONT_MAIN,
                )
                opt_menu["menu"].config(
                    bg=self.INPUT_BG,
                    fg=self.TEXT,
                    activebackground=self.ACCENT,
                    activeforeground="#ffffff",
                    font=self.FONT_MAIN,
                )
                opt_menu.pack(fill=tk.X, ipady=2)
            else:
                entry_frame = tk.Frame(field_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
                entry_frame.pack(fill=tk.X)

                entry_kwargs = {
                    "font": self.FONT_MAIN,
                    "bg": self.INPUT_BG,
                    "fg": self.TEXT_DIM,
                    "insertbackground": self.ACCENT,
                    "selectbackground": self.ACCENT,
                    "selectforeground": "#ffffff",
                    "relief": tk.FLAT,
                }
                if field_type == "password":
                    entry_kwargs["show"] = "*"

                entry = tk.Entry(
                    entry_frame,
                    **entry_kwargs
                )
                entry.insert(0, placeholder)

                self.run_inputs[field_name] = (entry, placeholder)

                def make_placeholder_handlers(e, p, is_pwd):
                    def on_focus_in(event):
                        if e.get() == p:
                            e.delete(0, tk.END)
                            e.configure(fg=self.TEXT)
                            if is_pwd:
                                e.configure(show="*")
                    def on_focus_out(event):
                        if not e.get():
                            e.insert(0, p)
                            e.configure(fg=self.TEXT_DIM)
                            if is_pwd:
                                e.configure(show="")
                    
                    if is_pwd:
                        if e.get() == p and p != "":
                            e.configure(show="")
                        else:
                            e.configure(show="*")
                            
                    e.bind("<FocusIn>", on_focus_in)
                    e.bind("<FocusOut>", on_focus_out)

                make_placeholder_handlers(entry, placeholder, (field_type == "password"))
                entry.pack(fill=tk.X, ipady=4, padx=6)

        # ▶ Run Automation button at the bottom of left column card
        submit_btn = tk.Button(
            form_frame,
            text="▶ Run Automation",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            command=lambda: self._on_run_simulation(workflow),
        )
        submit_btn.pack(anchor="w", pady=(10, 0))
        submit_btn.bind("<Enter>", lambda e: submit_btn.configure(bg=self.ACCENT_HOVER))
        submit_btn.bind("<Leave>", lambda e: submit_btn.configure(bg=self.ACCENT))

        # Right Column (Section D Output Panel container)
        self.right_col_container = right_col
        self._build_simulation_placeholder()

    def _build_simulation_placeholder(self) -> None:
        """Render a placeholder text in the execution logs space before submission."""
        for w in self.right_col_container.winfo_children():
            w.destroy()

        placeholder_lbl = tk.Label(
            self.right_col_container,
            text="⏳  Fill required inputs and click\n'Run Automation' to view simulated execution.",
            font=self.FONT_MAIN,
            fg=self.TEXT_DIM,
            bg=self.BG,
            justify=tk.CENTER,
        )
        placeholder_lbl.pack(expand=True)

    def _get_current_input_values(self) -> dict:
        """Gathers entered data from GUI dynamic form entries."""
        input_values = {}
        for field, item in self.run_inputs.items():
            if isinstance(item, tk.StringVar):
                input_values[field] = item.get()
            else:
                entry, placeholder = item
                val = entry.get().strip()
                if val == placeholder or not val:
                    input_values[field] = ""
                else:
                    input_values[field] = val
        return input_values

    def _on_run_simulation(self, workflow: dict) -> None:
        """Extract inputs and launch simulated run thread."""
        input_values = self._get_current_input_values()

        self.run_status_var.set("Simulating execution logs...")
        thread = Thread(
            target=self._run_simulation_thread,
            args=(workflow, input_values),
            daemon=True,
        )
        thread.start()

    def _run_simulation_thread(self, workflow: dict, input_values: dict) -> None:
        """Call sim executor in a background thread."""
        log_output = simulate_execution(workflow["id"], input_values)
        self.root.after(0, self._on_simulation_complete, log_output, workflow)

    def _on_simulation_complete(self, log_output: str, workflow: dict) -> None:
        """Updates the right column UI with the simulated results logs and buttons (Section D)."""
        self.run_status_var.set("✔  Simulation completed successfully.")
        
        for w in self.right_col_container.winfo_children():
            w.destroy()

        self.check_status_btn = None

        lbl_sim_title = tk.Label(
            self.right_col_container,
            text="Simulated Execution Log:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_sim_title.pack(fill=tk.X, pady=(0, 6))

        out_frame = tk.Frame(self.right_col_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
        out_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.sim_output_text = scrolledtext.ScrolledText(
            out_frame,
            wrap=tk.WORD,
            font=self.FONT_MONO,
            bg=self.INPUT_BG,
            fg=self.TEXT,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
            pady=8,
        )
        self.sim_output_text.pack(fill=tk.BOTH, expand=True)
        self.sim_output_text.insert(tk.END, log_output)
        self.sim_output_text.configure(state=tk.DISABLED)

        # Action Buttons row
        action_row = tk.Frame(self.right_col_container, bg=self.BG)
        action_row.pack(fill=tk.X)

        copy_sim_btn = tk.Button(
            action_row,
            text="📋  Copy Simulation Log",
            font=self.FONT_BTN,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.BORDER,
            activeforeground=self.TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._copy_sim_to_clipboard,
        )
        copy_sim_btn.pack(side=tk.LEFT, padx=(0, 10))
        copy_sim_btn.bind("<Enter>", lambda e: copy_sim_btn.configure(bg=self.BORDER))
        copy_sim_btn.bind("<Leave>", lambda e: copy_sim_btn.configure(bg=self.SURFACE))

        # ▶ Execute on AutomationEdge Button
        execute_btn = tk.Button(
            action_row,
            text="▶ Execute on AutomationEdge",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=lambda: self._on_execute_workflow(workflow),
        )
        execute_btn.pack(side=tk.LEFT)
        execute_btn.bind("<Enter>", lambda e: execute_btn.configure(bg=self.ACCENT_HOVER))
        execute_btn.bind("<Leave>", lambda e: execute_btn.configure(bg=self.ACCENT))

    def _copy_sim_to_clipboard(self) -> None:
        """Copies the simulated log text onto system clipboard."""
        content = self.sim_output_text.get("1.0", tk.END).strip()
        if not content:
            self.run_status_var.set("Nothing to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.run_status_var.set("✔  Copied simulation log to clipboard.")

    def _on_execute_workflow(self, workflow: dict) -> None:
        """Trigger workflow execution request in AutomationEdge backend."""
        # Step 1 — Check credentials
        from ae_config import AE_BASE_URL, AE_CLIENT_ID, AE_CLIENT_SECRET
        if not AE_BASE_URL or "your-ae-server" in AE_BASE_URL or not AE_CLIENT_ID or not AE_CLIENT_SECRET:
            messagebox.showwarning(
                "AutomationEdge Not Connected",
                "Real execution requires AutomationEdge credentials.\n\n"
                "Add AE_BASE_URL, AE_ORG_CODE, AE_CLIENT_ID, AE_CLIENT_SECRET to your .env file.\n\n"
                "Currently showing simulated output only."
            )
            return

        # Fetch current form inputs
        input_values = self._get_current_input_values()

        # Step 2 — Run in background thread
        self.sim_output_text.configure(state=tk.NORMAL)
        self.sim_output_text.delete("1.0", tk.END)
        self.sim_output_text.insert(tk.END, "Connecting to AutomationEdge...")
        self.sim_output_text.configure(state=tk.DISABLED)

        # Clear status buttons if present
        if self.check_status_btn:
            try:
                self.check_status_btn.destroy()
            except Exception:
                pass
            self.check_status_btn = None

        def run_execute():
            try:
                from ae_client import get_session_token, execute_workflow
                token = get_session_token()
                response = execute_workflow(token, workflow, input_values)
                self.root.after(0, self._on_execute_complete, response, workflow)
            except Exception as e:
                self.root.after(0, self._on_execute_failed, str(e))

        Thread(target=run_execute, daemon=True).start()

    def _on_execute_complete(self, response: dict, workflow: dict) -> None:
        """Renders success details or raises error dialog on failure."""
        if not response.get("success", True):
            self._on_execute_failed(response.get("error", "Execution failed"))
            return

        req_id = response.get("id") or response.get("requestId") or "N/A"
        status = response.get("status") or response.get("state") or "QUEUED"
        name = workflow.get("name")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success_text = (
            f"✓ Workflow Submitted to AutomationEdge\n"
            f"─────────────────────────────────────\n"
            f"Workflow:    {name}\n"
            f"Request ID:  {req_id}\n"
            f"Status:      {status}\n"
            f"Submitted:   {now_str}\n"
            f"Source:      RPA Spec Generator\n\n"
            f"Your workflow is now queued in AutomationEdge.\n"
            f"An agent will pick it up and execute it shortly.\n"
            f"─────────────────────────────────────"
        )

        self.sim_output_text.configure(state=tk.NORMAL)
        self.sim_output_text.delete("1.0", tk.END)
        self.sim_output_text.insert(tk.END, success_text)
        self.sim_output_text.configure(state=tk.DISABLED)

        # Step 3 — Add Check Status button below the output
        self._add_check_status_button(req_id)

    def _on_execute_failed(self, error_msg: str) -> None:
        """Renders error description to simulation output panel on submit fail."""
        fail_text = (
            f"✗ Execution Failed\n"
            f"─────────────────────────────────────\n"
            f"Error: {error_msg}\n\n"
            f"Possible reasons:\n"
            f"• Invalid credentials in .env\n"
            f"• Workflow not assigned to any agent\n"
            f"• AutomationEdge server unreachable\n"
            f"• Workflow name mismatch\n"
            f"─────────────────────────────────────"
        )

        self.sim_output_text.configure(state=tk.NORMAL)
        self.sim_output_text.delete("1.0", tk.END)
        self.sim_output_text.insert(tk.END, fail_text)
        self.sim_output_text.configure(state=tk.DISABLED)

    def _add_check_status_button(self, request_id) -> None:
        """Creates a Check Status button in output card space."""
        if self.check_status_btn:
            try:
                self.check_status_btn.destroy()
            except Exception:
                pass

        self.check_status_btn = tk.Button(
            self.right_col_container,
            text="🔍 Check Status",
            font=self.FONT_BTN,
            bg=self.SURFACE,
            fg=self.TEXT,
            activebackground=self.BORDER,
            activeforeground=self.TEXT,
            relief=tk.FLAT,
            cursor="hand2",
            padx=14,
            pady=6,
            command=lambda: self._on_check_status(request_id),
        )
        self.check_status_btn.pack(anchor="w", pady=(10, 0))
        self.check_status_btn.bind("<Enter>", lambda e: self.check_status_btn.configure(bg=self.BORDER))
        self.check_status_btn.bind("<Leave>", lambda e: self.check_status_btn.configure(bg=self.SURFACE))

    def _on_check_status(self, request_id) -> None:
        """Queries status of execution request in background thread."""
        self.check_status_btn.configure(state=tk.DISABLED, text="⏳ Checking...")

        def run_check():
            try:
                from ae_client import get_session_token, get_execution_status
                token = get_session_token()
                status_res = get_execution_status(token, str(request_id))
                self.root.after(0, self._on_check_status_complete, status_res)
            except Exception as e:
                self.root.after(0, self._on_check_status_failed, str(e))

        Thread(target=run_check, daemon=True).start()

    def _on_check_status_complete(self, response: dict) -> None:
        """Appends status response payload metadata to log text."""
        self.check_status_btn.configure(state=tk.NORMAL, text="🔍 Check Status")

        status = response.get("status") or response.get("state") or "UNKNOWN"
        updated_at = response.get("updatedDate") or response.get("lastUpdatedDate") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(updated_at, int):
            updated_at = datetime.fromtimestamp(updated_at / 1000.0).strftime("%Y-%m-%d %H:%M:%S")

        status_append = (
            f"\n\n[STATUS UPDATE]\n"
            f"Status:       {status}\n"
            f"Updated At:   {updated_at}\n"
            f"Response Msg: {response.get('message') or 'No message'}"
        )

        self.sim_output_text.configure(state=tk.NORMAL)
        self.sim_output_text.insert(tk.END, status_append)
        self.sim_output_text.see(tk.END)
        self.sim_output_text.configure(state=tk.DISABLED)

    def _on_check_status_failed(self, error_msg: str) -> None:
        """Appends status request failure warnings to log text."""
        self.check_status_btn.configure(state=tk.NORMAL, text="🔍 Check Status")
        error_append = f"\n\n[STATUS UPDATE FAILED]\nError: {error_msg}"

        self.sim_output_text.configure(state=tk.NORMAL)
        self.sim_output_text.insert(tk.END, error_append)
        self.sim_output_text.see(tk.END)
        self.sim_output_text.configure(state=tk.DISABLED)


def launch_gui(on_start=None) -> None:
    """Create the Tk root and start the application."""
    root = tk.Tk()
    RPASpecGeneratorApp(root)
    if on_start:
        root.after(1000, on_start)
    root.mainloop()
