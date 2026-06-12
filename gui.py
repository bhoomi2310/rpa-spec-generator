import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
from threading import Thread
from gemini_client import generate_spec
from catalog_client import detect_automation, simulate_execution, find_automation_by_id


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
        self._configure_window()
        self._build_ui()

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
        title = tk.Label(
            container,
            text="⚙  RPA Workflow Spec Generator",
            font=self.FONT_TITLE,
            fg=self.ACCENT,
            bg=self.BG,
            anchor="w",
        )
        title.pack(fill=tk.X, pady=(0, 14))

        # ── Notebook Tab Bar ──
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab Frames
        self.tab_spec = tk.Frame(self.notebook, bg=self.BG)
        self.tab_run = tk.Frame(self.notebook, bg=self.BG)

        self.notebook.add(self.tab_spec, text="Spec Generator")
        self.notebook.add(self.tab_run, text="Run Automation")

        # Build individual tabs
        self._build_tab_spec()
        self._build_tab_run()

    # ------------------------------------------------------------------ #
    #  TAB 1: Spec Generator (Existing Functionality)                   #
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
    #  TAB 2: Run Automation (New Functionality)                       #
    # ------------------------------------------------------------------ #
    def _build_tab_run(self) -> None:
        tab_container = tk.Frame(self.tab_run, bg=self.BG, pady=10)
        tab_container.pack(fill=tk.BOTH, expand=True)

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

        # Disable button & show loading state
        self.generate_btn.configure(state=tk.DISABLED, text="⏳  Generating…")
        self.status_var.set("Generating specification — please wait…")
        self._set_output("")

        thread = Thread(target=self._run_generation, args=(user_prompt,), daemon=True)
        thread.start()

    def _run_generation(self, user_prompt: str) -> None:
        """Runs in a background thread — calls Gemini and posts result back to UI."""
        result = generate_spec(user_prompt)
        # Schedule UI update on the main thread
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
    def _on_find_automation(self) -> None:
        """Starts background thread to detect catalog automation matching prompt."""
        prompt = self.run_prompt_entry.get().strip()
        if not prompt:
            messagebox.showwarning("Input Required", "Please describe what you want to automate.")
            return

        self.find_btn.configure(state=tk.DISABLED, text="⏳  Searching…")
        self.run_status_var.set("Searching automation catalog...")

        # Reset container
        for widget in self.run_container.winfo_children():
            widget.destroy()

        thread = Thread(target=self._run_detection, args=(prompt,), daemon=True)
        thread.start()

    def _run_detection(self, prompt: str) -> None:
        """Detect matched automation ID in a background thread."""
        detected_id = detect_automation(prompt)
        self.root.after(0, self._on_detection_complete, detected_id, prompt)

    def _on_detection_complete(self, detected_id: str, prompt: str) -> None:
        """Callback to main thread once automation search returns."""
        self.find_btn.configure(state=tk.NORMAL, text="🔍  Find Automation →")

        if not detected_id:
            self.run_status_var.set("No matching automation found.")
            self._build_no_match_ui(prompt)
        else:
            self.run_status_var.set(f"✔ Matched catalog entry: {detected_id}")
            self._build_matched_ui(detected_id)

    def _build_no_match_ui(self, prompt: str) -> None:
        """Create visual feedback panel when no match is found."""
        frame = tk.Frame(self.run_container, bg=self.BG, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl = tk.Label(
            frame,
            text="❌  No matching automation found.\n\nTry rephrasing or use the Spec Generator tab to create a new workflow spec.",
            font=self.FONT_MAIN,
            fg=self.TEXT_DIM,
            bg=self.BG,
            justify=tk.CENTER,
        )
        lbl.pack(pady=(20, 15))

        btn = tk.Button(
            frame,
            text="✦  Generate Spec Instead →",
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

    def _build_matched_ui(self, detected_id: str) -> None:
        """Renders Details, Dynamic Inputs Form, and Simulation Output layout."""
        automation = find_automation_by_id(detected_id)
        if not automation:
            return

        # Main horizontal splits
        main_split = tk.Frame(self.run_container, bg=self.BG)
        main_split.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(main_split, bg=self.BG)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        right_col = tk.Frame(main_split, bg=self.BG)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        # Left Column: SECTION B - Automation Found Card
        card = tk.Frame(left_col, bg=self.SURFACE, bd=1, relief=tk.SOLID, padx=15, pady=15)
        card.pack(fill=tk.X, pady=(0, 15))

        lbl_name = tk.Label(
            card,
            text=automation.get("name"),
            font=("Segoe UI", 13, "bold"),
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        lbl_name.pack(fill=tk.X, pady=(0, 5))

        lbl_desc = tk.Label(
            card,
            text=automation.get("description"),
            font=("Segoe UI", 10),
            fg=self.TEXT_DIM,
            bg=self.SURFACE,
            wraplength=350,
            justify=tk.LEFT,
            anchor="w",
        )
        lbl_desc.pack(fill=tk.X, pady=(0, 10))

        lbl_outputs_title = tk.Label(
            card,
            text="This automation will produce:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.SURFACE,
            anchor="w",
        )
        lbl_outputs_title.pack(fill=tk.X, pady=(0, 5))

        for out in automation.get("expected_outputs", []):
            lbl_out = tk.Label(
                card,
                text=f"  • {out}",
                font=("Segoe UI", 10),
                fg=self.TEXT_DIM,
                bg=self.SURFACE,
                anchor="w",
                justify=tk.LEFT,
                wraplength=330,
            )
            lbl_out.pack(fill=tk.X)

        # Left Column: SECTION C - Dynamic Input Form
        form_frame = tk.Frame(left_col, bg=self.BG)
        form_frame.pack(fill=tk.BOTH, expand=True)

        lbl_inputs_title = tk.Label(
            form_frame,
            text="Required Inputs:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_inputs_title.pack(fill=tk.X, pady=(0, 8))

        self.run_inputs = {}

        for inp in automation.get("required_inputs", []):
            field_name = inp["field"]
            field_label = inp["label"]
            field_type = inp["type"]
            placeholder = inp.get("placeholder", "")

            field_container = tk.Frame(form_frame, bg=self.BG, pady=4)
            field_container.pack(fill=tk.X)

            lbl_f = tk.Label(
                field_container,
                text=field_label,
                font=("Segoe UI", 10, "bold"),
                fg=self.TEXT_DIM,
                bg=self.BG,
                anchor="w",
            )
            lbl_f.pack(fill=tk.X, pady=(0, 3))

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
                opt_menu.pack(fill=tk.X, ipady=4)
            else:
                entry_frame = tk.Frame(field_container, bg=self.BORDER, bd=1, relief=tk.SOLID)
                entry_frame.pack(fill=tk.X)

                entry = tk.Entry(
                    entry_frame,
                    font=self.FONT_MAIN,
                    bg=self.INPUT_BG,
                    fg=self.TEXT_DIM,
                    insertbackground=self.ACCENT,
                    selectbackground=self.ACCENT,
                    selectforeground="#ffffff",
                    relief=tk.FLAT,
                )
                entry.insert(0, placeholder)

                self.run_inputs[field_name] = (entry, placeholder)

                # Configure dynamic placeholder handlers
                def make_placeholder_handlers(e, p):
                    def on_focus_in(event):
                        if e.get() == p:
                            e.delete(0, tk.END)
                            e.configure(fg=self.TEXT)
                    def on_focus_out(event):
                        if not e.get():
                            e.insert(0, p)
                            e.configure(fg=self.TEXT_DIM)
                    e.bind("<FocusIn>", on_focus_in)
                    e.bind("<FocusOut>", on_focus_out)

                make_placeholder_handlers(entry, placeholder)
                entry.pack(fill=tk.X, ipady=6, padx=8)

        # Run button
        submit_btn = tk.Button(
            form_frame,
            text="⚙  Run Automation",
            font=self.FONT_BTN,
            bg=self.ACCENT,
            fg="#ffffff",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            command=lambda: self._on_run_simulation(detected_id),
        )
        submit_btn.pack(anchor="w", pady=(15, 0))
        submit_btn.bind("<Enter>", lambda e: submit_btn.configure(bg=self.ACCENT_HOVER))
        submit_btn.bind("<Leave>", lambda e: submit_btn.configure(bg=self.ACCENT))

        # Right Column: SECTION D - Simulation Output Panel
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

    def _on_run_simulation(self, automation_id: str) -> None:
        """Extract inputs and launch simulated run thread."""
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

        self.run_status_var.set("Simulating execution logs...")
        thread = Thread(
            target=self._run_simulation_thread,
            args=(automation_id, input_values),
            daemon=True,
        )
        thread.start()

    def _run_simulation_thread(self, automation_id: str, input_values: dict) -> None:
        """Call sim executor in a background thread."""
        log_output = simulate_execution(automation_id, input_values)
        self.root.after(0, self._on_simulation_complete, log_output)

    def _on_simulation_complete(self, log_output: str) -> None:
        """Updates the right column UI with the simulated results logs."""
        self.run_status_var.set("✔  Simulation completed successfully.")
        
        for w in self.right_col_container.winfo_children():
            w.destroy()

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

        # Copy Simulation logs Button
        copy_sim_btn = tk.Button(
            self.right_col_container,
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
        copy_sim_btn.pack(anchor="w")
        copy_sim_btn.bind("<Enter>", lambda e: copy_sim_btn.configure(bg=self.BORDER))
        copy_sim_btn.bind("<Leave>", lambda e: copy_sim_btn.configure(bg=self.SURFACE))

    def _copy_sim_to_clipboard(self) -> None:
        """Copies the simulated log text onto system clipboard."""
        content = self.sim_output_text.get("1.0", tk.END).strip()
        if not content:
            self.run_status_var.set("Nothing to copy.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.run_status_var.set("✔  Copied simulation log to clipboard.")


def launch_gui() -> None:
    """Create the Tk root and start the application."""
    root = tk.Tk()
    RPASpecGeneratorApp(root)
    root.mainloop()
