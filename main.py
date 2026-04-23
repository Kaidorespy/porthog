"""PortHog - See what's hogging your ports. Kill it."""

import psutil
import ctypes
import sys
import os
import threading
import time
from collections import defaultdict
import customtkinter as ctk
from tkinter import messagebox

# Check admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class PortHog(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PortHog")
        self.geometry("700x500")
        self.minsize(500, 300)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.connections = []
        self.auto_refresh = True
        self.paused = False

        self._build_ui()
        self._refresh()

        # Auto-refresh thread
        self._start_auto_refresh()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=15, pady=15)

        ctk.CTkLabel(header, text="PortHog", font=('Segoe UI', 20, 'bold')).pack(side='left')

        # Controls
        ctrl = ctk.CTkFrame(header, fg_color='transparent')
        ctrl.pack(side='right')

        self.refresh_btn = ctk.CTkButton(ctrl, text="Refresh", width=80, command=lambda: self._refresh(force=True))
        self.refresh_btn.pack(side='left', padx=5)

        self.pause_btn = ctk.CTkButton(ctrl, text="Freeze", width=70, fg_color='#444',
                                        command=self._toggle_pause)
        self.pause_btn.pack(side='left', padx=5)

        self.auto_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(ctrl, text="Auto (30s)", variable=self.auto_var,
                        command=self._toggle_auto).pack(side='left', padx=10)

        # Filter
        filter_frame = ctk.CTkFrame(self, fg_color='transparent')
        filter_frame.pack(fill='x', padx=15, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filter:").pack(side='left')
        self.filter_var = ctk.StringVar()
        self.filter_var.trace('w', lambda *a: self._apply_filter())
        self.filter_entry = ctk.CTkEntry(filter_frame, textvariable=self.filter_var,
                                          width=150, placeholder_text="port or process name")
        self.filter_entry.pack(side='left', padx=10)

        self.count_label = ctk.CTkLabel(filter_frame, text="", text_color='gray')
        self.count_label.pack(side='right')

        # Table header
        table_header = ctk.CTkFrame(self, fg_color='#2a2a2a')
        table_header.pack(fill='x', padx=15)

        cols = [("Port", 80), ("Proto", 50), ("State", 90), ("PID", 60), ("Process", 200), ("", 80)]
        for text, width in cols:
            ctk.CTkLabel(table_header, text=text, width=width, anchor='w',
                        font=('Segoe UI', 11, 'bold')).pack(side='left', padx=5, pady=8)

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(self, fg_color='transparent')
        self.scroll.pack(fill='both', expand=True, padx=15, pady=(5, 15))

    def _refresh(self, force=False):
        """Refresh connection list."""
        if self.paused and not force:
            return

        self.connections = []

        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr:
                    port = conn.laddr.port
                    proto = 'TCP' if conn.type == 1 else 'UDP'
                    state = conn.status if hasattr(conn, 'status') else 'N/A'
                    pid = conn.pid or 0

                    # Get process name
                    proc_name = ""
                    if pid:
                        try:
                            proc = psutil.Process(pid)
                            proc_name = proc.name()
                        except:
                            proc_name = "(unknown)"

                    self.connections.append({
                        'port': port,
                        'proto': proto,
                        'state': state,
                        'pid': pid,
                        'name': proc_name
                    })
        except psutil.AccessDenied:
            pass

        # Sort by port
        self.connections.sort(key=lambda x: x['port'])

        # Remove duplicates (same port/proto/pid)
        seen = set()
        unique = []
        for c in self.connections:
            key = (c['port'], c['proto'], c['pid'])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        self.connections = unique

        self._apply_filter()

    def _apply_filter(self):
        """Apply port filter and display."""
        # Clear existing
        for widget in self.scroll.winfo_children():
            widget.destroy()

        filter_text = self.filter_var.get().strip().lower()

        displayed = []
        for conn in self.connections:
            if filter_text:
                # Match port number or process name
                port_match = filter_text in str(conn['port'])
                name_match = filter_text in conn['name'].lower()
                if not port_match and not name_match:
                    continue
            displayed.append(conn)

        self.count_label.configure(text=f"{len(displayed)} connections")

        # Show rows
        for conn in displayed[:100]:  # Limit display
            self._add_row(conn)

    def _add_row(self, conn):
        """Add a connection row."""
        row = ctk.CTkFrame(self.scroll, fg_color='#1e1e1e', corner_radius=5)
        row.pack(fill='x', pady=2)

        # Port
        port_color = '#ff6b6b' if conn['port'] < 1024 else '#ffffff'
        ctk.CTkLabel(row, text=str(conn['port']), width=80, anchor='w',
                    text_color=port_color, font=('Consolas', 11)).pack(side='left', padx=5, pady=8)

        # Proto
        ctk.CTkLabel(row, text=conn['proto'], width=50, anchor='w',
                    text_color='gray').pack(side='left', padx=5)

        # State
        state_color = '#4ade80' if conn['state'] == 'LISTEN' else '#888888'
        ctk.CTkLabel(row, text=conn['state'], width=90, anchor='w',
                    text_color=state_color).pack(side='left', padx=5)

        # PID
        ctk.CTkLabel(row, text=str(conn['pid']) if conn['pid'] else '-', width=60, anchor='w',
                    text_color='gray', font=('Consolas', 10)).pack(side='left', padx=5)

        # Process name
        ctk.CTkLabel(row, text=conn['name'][:30], width=200, anchor='w').pack(side='left', padx=5)

        # Kill button
        if conn['pid'] and conn['pid'] != os.getpid():
            kill_btn = ctk.CTkButton(row, text="Kill", width=60, height=24,
                                      fg_color='#8b0000', hover_color='#a52a2a',
                                      command=lambda p=conn['pid'], n=conn['name']: self._kill(p, n))
            kill_btn.pack(side='right', padx=10, pady=5)

    def _kill(self, pid, name):
        """Kill a process."""
        if not messagebox.askyesno("Kill Process", f"Kill {name} (PID {pid})?"):
            return

        try:
            proc = psutil.Process(pid)
            proc.terminate()
            time.sleep(0.5)
            if proc.is_running():
                proc.kill()
            self._refresh()
        except psutil.NoSuchProcess:
            self._refresh()
        except psutil.AccessDenied:
            messagebox.showerror("Error", "Access denied. Try running as admin.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _toggle_auto(self):
        """Toggle auto-refresh."""
        self.auto_refresh = self.auto_var.get()

    def _toggle_pause(self):
        """Toggle freeze display."""
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.configure(text="Unfreeze", fg_color='#8b0000')
        else:
            self.pause_btn.configure(text="Freeze", fg_color='#444')
            self._refresh()

    def _start_auto_refresh(self):
        """Start auto-refresh thread."""
        def loop():
            while True:
                time.sleep(30)
                if self.auto_refresh:
                    self.after(0, self._refresh)

        t = threading.Thread(target=loop, daemon=True)
        t.start()


if __name__ == "__main__":
    # Suggest admin if not
    if not is_admin():
        print("Tip: Run as admin to see all connections and kill system processes")

    app = PortHog()
    app.mainloop()
