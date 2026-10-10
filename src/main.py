from __future__ import annotations

import json
import math
import re
import sys
import threading
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from tkinter import messagebox, ttk
from uuid import uuid4


MAX_CHARTS = 4
COLORS = ("#6986c8", "#70aaa1", "#a287bc", "#d9a36c", "#76a27a", "#cf7f7f")


def fetch_dashboard_data(search_text: str) -> dict[str, Any] | None:
    """Load the dashboard associated with a search option in data.json."""
    data_path = Path(__file__).with_name("data.json")
    with data_path.open(encoding="utf-8") as data_file:
        search_options = json.load(data_file)

    if not isinstance(search_options, dict):
        raise ValueError("data.json must contain an object of search options.")

    query = " ".join(search_text.casefold().split())
    if not query:
        return None

    normalized_keys = {
        " ".join(key.casefold().split()): key
        for key in search_options
        if isinstance(key, str)
    }
    exact_match = normalized_keys.get(query)
    matching_keys = [
        key
        for key in search_options
        if isinstance(key, str) and query in " ".join(key.casefold().split())
    ]
    if exact_match is not None:
        matching_keys = [exact_match]
    if len(matching_keys) != 1:
        return None

    dashboard = search_options[matching_keys[0]]
    if not isinstance(dashboard, dict):
        raise ValueError(f"The data for '{matching_keys[0]}' must be an object.")
    return dashboard


def _field(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    fields = {str(key).casefold(): value for key, value in data.items()}
    for name in names:
        if name.casefold() in fields:
            return fields[name.casefold()]
    return default


def _chart_definitions(data: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    chart_entries = [
        (key, value)
        for key, value in data.items()
        if re.fullmatch(r"chart\d+", str(key), flags=re.IGNORECASE)
        and isinstance(value, dict)
    ]
    chart_entries.sort(key=lambda entry: int(re.findall(r"\d+", entry[0])[0]))

    raw_count = _field(data, "Number of Charts", "number_of_charts", default=None)
    warning = None
    if raw_count is not None:
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            count = len(chart_entries)
            warning = "The chart count is invalid; displaying the charts found."
        if count > MAX_CHARTS:
            warning = f"Only the first {MAX_CHARTS} charts are supported."
            count = MAX_CHARTS
        if count < 0:
            warning = "The chart count cannot be negative."
            count = 0
        chart_entries = chart_entries[:count]

    if len(chart_entries) > MAX_CHARTS:
        warning = f"Only the first {MAX_CHARTS} charts are supported."
        chart_entries = chart_entries[:MAX_CHARTS]
    return [chart for _, chart in chart_entries], warning


class EconLandApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EconLand | Economy + Land")
        self.geometry("900x620")
        self.minsize(760, 540)
        self.configure(bg="#f5f4f0")
        self._build_home()

    def _build_home(self) -> None:
        header = tk.Frame(self, bg="#344d50", padx=40, pady=32)
        header.pack(fill="x")
        tk.Label(
            header,
            text="EconLand",
            bg="#344d50",
            fg="#ffffff",
            font=("Segoe UI", 28, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Explore the connection between economic growth and land.",
            bg="#344d50",
            fg="#d4dfd8",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(5, 0))

        content = tk.Frame(self, bg="#f5f4f0", padx=40, pady=36)
        content.pack(fill="both", expand=True)
        tk.Label(
            content,
            text="What would you like to do?",
            bg="#f5f4f0",
            fg="#344d50",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w", pady=(0, 7))
        tk.Label(
            content,
            text="Explore a topic or tell your local community about a land issue.",
            bg="#f5f4f0",
            fg="#64716d",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 24))

        choices = tk.Frame(content, bg="#f5f4f0")
        choices.pack(fill="x")
        self._home_card(
            choices,
            "Explore EconLand",
            "Search topics and explore their summaries, data, and charts.",
            "Search topics",
            self._open_search,
            0,
        )
        self._home_card(
            choices,
            "Report a land issue",
            "Share a concern about land, water, pollution, or the local environment.",
            "Create a report",
            self._open_report,
            1,
        )

        tk.Label(
            content,
            text="Reports are saved on this device. This demo does not send them to a government office.",
            bg="#f5f4f0",
            fg="#64716d",
            wraplength=700,
            justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(22, 0))

    @staticmethod
    def _home_card(
        parent: tk.Frame,
        title: str,
        description: str,
        button_text: str,
        command: Any,
        column: int,
    ) -> None:
        card = tk.Frame(parent, bg="#ffffff", padx=22, pady=22)
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 10) if column == 0 else (10, 0))
        parent.grid_columnconfigure(column, weight=1, uniform="home_cards")
        tk.Label(
            card,
            text=title,
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            card,
            text=description,
            bg="#ffffff",
            fg="#64716d",
            justify="left",
            anchor="w",
            wraplength=330,
            height=3,
            font=("Segoe UI", 10),
        ).pack(fill="x", pady=(10, 18))
        tk.Button(
            card,
            text=button_text,
            command=command,
            bg="#536f9e",
            fg="#ffffff",
            activebackground="#405b86",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(anchor="w")

    def _open_search(self) -> None:
        SearchWindow(self)

    def _open_report(self) -> None:
        ReportWindow(self)


class SearchWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Explore EconLand")
        self.geometry("1080x760")
        self.minsize(820, 620)
        self.configure(bg="#f5f4f0")
        self._build_styles()
        self._build_layout()

    def _build_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f4f0")
        style.configure(
            "Search.TEntry",
            fieldbackground="#ffffff",
            padding=(12, 10),
            font=("Segoe UI", 11),
        )
        style.configure(
            "Search.TButton",
            background="#536f9e",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padding=(18, 10),
        )
        style.map(
            "Search.TButton",
            background=[("active", "#405b86"), ("disabled", "#aab4c4")],
        )

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg="#344d50", padx=32, pady=24)
        header.pack(fill="x")
        header_row = tk.Frame(header, bg="#344d50")
        header_row.pack(fill="x")
        tk.Button(
            header_row,
            text="← Home",
            command=self.destroy,
            bg="#496365",
            fg="#ffffff",
            activebackground="#40595b",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="right")
        tk.Label(
            header_row,
            text="EconLand",
            bg="#344d50",
            fg="#ffffff",
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Explore the connection between economic growth and land.",
            bg="#344d50",
            fg="#d4dfd8",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        search_card = tk.Frame(self, bg="#ffffff", padx=22, pady=19)
        search_card.pack(fill="x", padx=24, pady=(20, 14))
        tk.Label(
            search_card,
            text="What would you like to explore?",
            bg="#ffffff",
            fg="#475569",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        search_row = tk.Frame(search_card, bg="#ffffff")
        search_row.pack(fill="x")
        self.search_entry = ttk.Entry(search_row, style="Search.TEntry")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", self._search)
        self.search_button = ttk.Button(
            search_row,
            text="Search",
            style="Search.TButton",
            command=self._search,
        )
        self.search_button.pack(side="right")

        body = ttk.Frame(self, padding=(24, 0, 24, 8))
        body.pack(fill="both", expand=True)
        self.dashboard_canvas = tk.Canvas(
            body, bg="#f5f4f0", highlightthickness=0, borderwidth=0
        )
        scrollbar = ttk.Scrollbar(
            body, orient="vertical", command=self.dashboard_canvas.yview
        )
        self.dashboard_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.dashboard_canvas.pack(side="left", fill="both", expand=True)
        self.dashboard = tk.Frame(self.dashboard_canvas, bg="#f5f4f0")
        self.dashboard_window = self.dashboard_canvas.create_window(
            (0, 0), window=self.dashboard, anchor="nw"
        )
        self.dashboard.bind("<Configure>", self._update_scroll_region)
        self.dashboard_canvas.bind("<Configure>", self._resize_dashboard)
        self.bind_all("<MouseWheel>", self._scroll_dashboard)

        self.status = tk.Label(
            self,
            text="Search for a place, topic, or indicator. Example data is ready to explore.",
            bg="#e8e7e1",
            fg="#475569",
            anchor="w",
            padx=24,
            pady=8,
            font=("Segoe UI", 9),
        )
        self.status.pack(fill="x", side="bottom")
        self.search_entry.focus_set()
        self._show_message(
            "Search for an economy or land topic to see a sample dashboard."
        )

    def _update_scroll_region(self, _event: tk.Event | None = None) -> None:
        self.dashboard_canvas.configure(
            scrollregion=self.dashboard_canvas.bbox("all")
        )

    def _resize_dashboard(self, event: tk.Event) -> None:
        self.dashboard_canvas.itemconfigure(self.dashboard_window, width=event.width)

    def _scroll_dashboard(self, event: tk.Event) -> None:
        if self.dashboard_canvas.winfo_exists():
            self.dashboard_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _search(self, _event: tk.Event | None = None) -> None:
        search_text = self.search_entry.get().strip()
        if not search_text:
            messagebox.showinfo("Just one thing", "Enter a topic to get started.")
            self.search_entry.focus_set()
            return

        self.search_button.configure(state="disabled")
        self.status.configure(text=f"Looking up {search_text}...")
        self._clear_dashboard()
        self._show_message("Putting the details together...")
        threading.Thread(
            target=self._load_dashboard,
            args=(search_text,),
            daemon=True,
        ).start()

    def _load_dashboard(self, search_text: str) -> None:
        try:
            data = fetch_dashboard_data(search_text)
        except (TypeError, ValueError) as error:
            self.after(0, self._show_error, str(error))
        except OSError as error:
            self.after(
                0,
                self._show_error,
                f"Could not read data.json: {error}",
            )
        else:
            self.after(0, self._render_result, data)

    def _render_result(self, data: dict[str, Any] | None) -> None:
        self.search_button.configure(state="normal")
        self._clear_dashboard()
        if data is None:
            self.status.configure(text="No matching record found.")
            self._show_message("No matching data found. Try another topic.")
            return

        title = str(_field(data, "name", "title", default="Search result"))
        about = _field(data, "ABOut", "about")
        overview = _field(data, "overview")
        charts, warning = _chart_definitions(data)
        self.status.configure(
            text=f"Showing {title}" + (f"  |  {warning}" if warning else "")
        )

        if title != "Search result" or about or overview:
            summary = tk.Frame(self.dashboard, bg="#ffffff", padx=22, pady=19)
            summary.pack(fill="x", pady=(0, 14))
            tk.Label(
                summary,
                text=title,
                bg="#ffffff",
                fg="#344d50",
                font=("Segoe UI", 16, "bold"),
            ).pack(anchor="w")
            if about:
                self._text_block(summary, "About this view", about, top_padding=10)
            if overview:
                self._text_block(summary, "The big picture", overview, top_padding=12)

        if charts:
            chart_grid = tk.Frame(self.dashboard, bg="#f5f4f0")
            chart_grid.pack(fill="both", expand=True)
            for index, chart in enumerate(charts):
                card = tk.Frame(chart_grid, bg="#ffffff", padx=20, pady=18)
                card.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="nsew",
                    padx=(0, 8) if index % 2 == 0 else (8, 0),
                    pady=(0, 14),
                )
                chart_grid.grid_columnconfigure(index % 2, weight=1, uniform="charts")
                self._render_chart(card, chart)

        known_fields = {
            "name", "title", "about", "overview", "number of charts",
            "number_of_charts", "_id",
        }
        extra_fields = {
            key: value
            for key, value in data.items()
            if str(key).casefold() not in known_fields
            and not re.fullmatch(r"chart\d+", str(key), flags=re.IGNORECASE)
        }
        if extra_fields:
            extra_card = tk.Frame(self.dashboard, bg="#ffffff", padx=18, pady=15)
            extra_card.pack(fill="x", pady=(0, 14))
            tk.Label(
                extra_card,
                text="A few more details",
                bg="#ffffff",
                fg="#475569",
                font=("Segoe UI", 9, "bold"),
            ).pack(anchor="w", pady=(0, 8))
            tk.Label(
                extra_card,
                text=self._format_fields(extra_fields),
                justify="left",
                anchor="w",
                wraplength=900,
                bg="#ffffff",
                fg="#334155",
                font=("Segoe UI", 10),
            ).pack(fill="x")

        if not (about or overview or charts or extra_fields):
            self._show_message("There isn't any extra information to show yet.")

    def _render_chart(self, parent: tk.Frame, chart: dict[str, Any]) -> None:
        title = str(_field(chart, "title", default="Chart"))
        chart_type = str(_field(chart, "type", default="")).casefold()
        content = _field(chart, "content")
        labels = _field(chart, "Labels", "labels", default=[])
        values = _field(chart, "dataset1", "values", default=[])

        tk.Label(
            parent,
            text=title,
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")
        if content:
            tk.Label(
                parent,
                text=str(content),
                bg="#ffffff",
                fg="#64748b",
                justify="left",
                wraplength=460,
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(5, 8))

        try:
            chart_labels, chart_values = self._clean_chart_data(labels, values)
            if "bar" in chart_type:
                self._draw_bar_chart(parent, chart_labels, chart_values)
            elif "pie" in chart_type:
                self._draw_pie_chart(parent, chart_labels, chart_values)
            else:
                raise ValueError("Chart type must be 'bar graph' or 'piechart'.")
        except ValueError as error:
            tk.Label(
                parent,
                text=f"Couldn't draw this chart: {error}",
                bg="#f8f0e8",
                fg="#805b3d",
                justify="left",
                wraplength=460,
                padx=10,
                pady=10,
                font=("Segoe UI", 9),
            ).pack(fill="x", pady=(8, 0))

    @staticmethod
    def _clean_chart_data(labels: Any, values: Any) -> tuple[list[str], list[float]]:
        if not isinstance(labels, (list, tuple)) or not isinstance(values, (list, tuple)):
            raise ValueError("Labels and dataset1 must both be lists.")
        if not labels or len(labels) != len(values):
            raise ValueError("Labels and dataset1 must contain the same non-zero number of items.")
        clean_values: list[float] = []
        for value in values:
            if isinstance(value, bool):
                raise ValueError("Chart values must be numeric.")
            try:
                number = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError("Chart values must be numeric.") from error
            if not math.isfinite(number):
                raise ValueError("Chart values must be finite numbers.")
            clean_values.append(number)
        if any(value < 0 for value in clean_values):
            raise ValueError("Chart values cannot be negative.")
        return [str(label) for label in labels], clean_values

    @staticmethod
    def _draw_bar_chart(
        parent: tk.Frame, labels: list[str], values: list[float]
    ) -> None:
        canvas = tk.Canvas(
            parent, height=240, bg="#ffffff", highlightthickness=0
        )
        canvas.pack(fill="x", pady=(4, 0))
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 360)
        height = 240
        left, right, top, bottom = 46, width - 16, 16, height - 60
        max_value = max(values) or 1
        canvas.create_line(left, top, left, bottom, fill="#cbd5e1")
        canvas.create_line(left, bottom, right, bottom, fill="#cbd5e1")

        step = (right - left) / max(len(values), 1)
        bar_width = min(46, step * 0.62)
        for index, (label, value) in enumerate(zip(labels, values)):
            center = left + step * (index + 0.5)
            bar_top = bottom - (bottom - top) * (value / max_value)
            canvas.create_rectangle(
                center - bar_width / 2,
                bar_top,
                center + bar_width / 2,
                bottom,
                fill=COLORS[index % len(COLORS)],
                outline="",
            )
            canvas.create_text(
                center,
                max(bar_top - 9, top),
                text=f"{value:g}",
                fill="#475569",
                font=("Segoe UI", 8),
            )
            short_label = label if len(label) <= 12 else label[:11] + "..."
            canvas.create_text(
                center,
                bottom + 17,
                text=short_label,
                fill="#64748b",
                font=("Segoe UI", 8),
            )

    @staticmethod
    def _draw_pie_chart(
        parent: tk.Frame, labels: list[str], values: list[float]
    ) -> None:
        total = sum(values)
        if total <= 0:
            raise ValueError("A pie chart needs a total greater than zero.")

        chart_row = tk.Frame(parent, bg="#ffffff")
        chart_row.pack(fill="x", pady=(6, 0))
        canvas = tk.Canvas(
            chart_row, width=220, height=205, bg="#ffffff", highlightthickness=0
        )
        canvas.pack(side="left")
        start_angle = 90
        for index, value in enumerate(values):
            extent = value / total * 360
            canvas.create_arc(
                18,
                10,
                202,
                194,
                start=start_angle,
                extent=-extent,
                fill=COLORS[index % len(COLORS)],
                outline="#ffffff",
                width=2,
                style="pieslice",
            )
            start_angle -= extent

        legend = tk.Frame(chart_row, bg="#ffffff", padx=8, pady=8)
        legend.pack(side="left", fill="both", expand=True)
        for index, (label, value) in enumerate(zip(labels, values)):
            row = tk.Frame(legend, bg="#ffffff")
            row.pack(anchor="w", fill="x", pady=3)
            tk.Label(
                row,
                text="●",
                fg=COLORS[index % len(COLORS)],
                bg="#ffffff",
                font=("Segoe UI", 11),
            ).pack(side="left", padx=(0, 6))
            tk.Label(
                row,
                text=f"{label}: {value:g} ({value / total:.0%})",
                fg="#475569",
                bg="#ffffff",
                anchor="w",
                font=("Segoe UI", 9),
            ).pack(side="left", fill="x")

    @staticmethod
    def _text_block(
        parent: tk.Frame, heading: str, text: Any, top_padding: int
    ) -> None:
        tk.Label(
            parent,
            text=heading.title(),
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(top_padding, 4))
        tk.Label(
            parent,
            text=str(text),
            bg="#ffffff",
            fg="#334155",
            justify="left",
            anchor="w",
            wraplength=940,
            font=("Segoe UI", 10),
        ).pack(fill="x")

    @staticmethod
    def _format_fields(fields: dict[str, Any]) -> str:
        return "\n".join(f"{key}: {value}" for key, value in fields.items())

    def _show_message(self, text: str) -> None:
        self._clear_dashboard()
        tk.Label(
            self.dashboard,
            text=text,
            bg="#ffffff",
            fg="#64716d",
            padx=20,
            pady=24,
            font=("Segoe UI", 10),
        ).pack(fill="x")

    def _show_error(self, text: str) -> None:
        self.search_button.configure(state="normal")
        self.status.configure(text="That search ran into a problem.")
        self._show_message(text)

    def _clear_dashboard(self) -> None:
        for child in self.dashboard.winfo_children():
            child.destroy()


class ReportWindow(tk.Toplevel):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.title("Report a land issue | EconLand")
        self.geometry("760x700")
        self.minsize(650, 600)
        self.configure(bg="#f5f4f0")
        self._build_form()

    def _build_form(self) -> None:
        header = tk.Frame(self, bg="#344d50", padx=30, pady=20)
        header.pack(fill="x")
        header_row = tk.Frame(header, bg="#344d50")
        header_row.pack(fill="x")
        tk.Button(
            header_row,
            text="← Home",
            command=self.destroy,
            bg="#496365",
            fg="#ffffff",
            activebackground="#40595b",
            activeforeground="#ffffff",
            relief="flat",
            padx=12,
            pady=6,
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="right")
        tk.Label(
            header_row,
            text="Report a land issue",
            bg="#344d50",
            fg="#ffffff",
            font=("Segoe UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Share a local concern so it can be reviewed and followed up.",
            bg="#344d50",
            fg="#d4dfd8",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(self, bg="#ffffff", padx=26, pady=22)
        form.pack(fill="both", expand=True, padx=26, pady=20)
        tk.Label(
            form,
            text="Location *",
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        self.location_entry = ttk.Entry(form, font=("Segoe UI", 10))
        self.location_entry.pack(fill="x", pady=(0, 15), ipady=5)

        tk.Label(
            form,
            text="What is the issue about?",
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        self.category = ttk.Combobox(
            form,
            state="readonly",
            values=(
                "Land degradation",
                "Deforestation",
                "Water pollution or shortage",
                "Waste or pollution",
                "Unsafe land use",
                "Other",
            ),
            font=("Segoe UI", 10),
        )
        self.category.current(0)
        self.category.pack(fill="x", pady=(0, 15), ipady=4)

        tk.Label(
            form,
            text="Describe what you noticed *",
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        self.description = tk.Text(
            form,
            height=8,
            wrap="word",
            bg="#fbfbf9",
            fg="#334155",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=9,
            pady=8,
        )
        self.description.pack(fill="both", expand=True, pady=(0, 15))

        tk.Label(
            form,
            text="Your name (optional)",
            bg="#ffffff",
            fg="#344d50",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        self.reporter_entry = ttk.Entry(form, font=("Segoe UI", 10))
        self.reporter_entry.pack(fill="x", pady=(0, 12), ipady=5)

        tk.Label(
            form,
            text="Reports are saved on this device only. They are not sent to a government office.",
            bg="#ffffff",
            fg="#805b3d",
            wraplength=640,
            justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 13))
        tk.Button(
            form,
            text="Save report",
            command=self._save_report,
            bg="#536f9e",
            fg="#ffffff",
            activebackground="#405b86",
            activeforeground="#ffffff",
            relief="flat",
            padx=18,
            pady=9,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(anchor="e")

    def _save_report(self) -> None:
        location = self.location_entry.get().strip()
        description = self.description.get("1.0", "end").strip()
        if not location or not description:
            messagebox.showwarning(
                "A little more information",
                "Please enter the location and describe the issue.",
                parent=self,
            )
            return

        report = {
            "report_id": str(uuid4()),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "location": location,
            "category": self.category.get(),
            "description": description,
            "reporter_name": self.reporter_entry.get().strip() or None,
            "delivery_status": "saved_locally_not_sent",
        }
        app_directory = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent
        )
        report_path = app_directory / "reports.jsonl"
        try:
            with report_path.open("a", encoding="utf-8") as report_file:
                report_file.write(json.dumps(report, ensure_ascii=False) + "\n")
        except OSError as error:
            messagebox.showerror(
                "Couldn't save the report",
                f"Please check that the app folder is writable.\n\n{error}",
                parent=self,
            )
            return

        messagebox.showinfo(
            "Report saved",
            "Your report was saved on this device. It has not been sent to a government office.\n\n"
            f"Saved to: {report_path}",
            parent=self,
        )
        self.location_entry.delete(0, tk.END)
        self.description.delete("1.0", tk.END)
        self.reporter_entry.delete(0, tk.END)
        self.category.current(0)


if __name__ == "__main__":
    EconLandApp().mainloop()
