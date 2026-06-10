import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from threading import Thread
from gemini_client import generate_spec


class RPASpecGeneratorApp:
    """Desktop GUI for generating RPA workflow specifications."""

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
        title.pack(fill=tk.X, pady=(0, 18))

        # ── Input label ──
        lbl_input = tk.Label(
            container,
            text="Describe your automation:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_input.pack(fill=tk.X, pady=(0, 6))

        # ── Input text area ──
        input_frame = tk.Frame(container, bg=self.BORDER, bd=1, relief=tk.SOLID)
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

        # ── Generate button ──
        self.generate_btn = tk.Button(
            container,
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

        # ── Output label ──
        lbl_output = tk.Label(
            container,
            text="Generated Specification:",
            font=self.FONT_LABEL,
            fg=self.TEXT,
            bg=self.BG,
            anchor="w",
        )
        lbl_output.pack(fill=tk.X, pady=(0, 6))

        # ── Output text area (scrollable) ──
        output_frame = tk.Frame(container, bg=self.BORDER, bd=1, relief=tk.SOLID)
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

        # ── Status label ──
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            container,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            fg=self.TEXT_DIM,
            bg=self.BG,
            anchor="w",
        )
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        # ── Action buttons row ──
        btn_row = tk.Frame(container, bg=self.BG)
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
    #  Event handlers                                                     #
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


def launch_gui() -> None:
    """Create the Tk root and start the application."""
    root = tk.Tk()
    RPASpecGeneratorApp(root)
    root.mainloop()
