
"""Desktop interface for AttendancePro."""

import csv
import datetime
import re
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.interpolate import make_interp_spline

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "sidebar": "#050505", "main": "#0A0A0B", "card": "#111113",
    "purple":  "#8B5CF6", "purple2": "#7C3AED",
    "white":   "#F8FAFC", "muted":   "#94A3B8",
    "border":  "#27272A", "border2": "#3F3F46",
    "gold":    "#FBBF24", "red":     "#EF4444",
    "green":   "#10B981", "blue":    "#3B82F6",
}

APP = "AttendancePro"
VER = "2.5"

BIG   = ("Segoe UI", 26, "bold")
HEAD  = ("Segoe UI", 16, "bold")
BODY  = ("Segoe UI", 13)
BOLD  = ("Segoe UI", 12, "bold")
SMALL = ("Segoe UI", 11)
TINY  = ("Segoe UI", 10)


def _tint(hex_color, alpha=0.15, bg="#111113"):
    """Blend a colour at given opacity over the card background."""
    r1, g1, b1 = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    r2, g2, b2 = int(bg[1:3], 16),        int(bg[3:5], 16),        int(bg[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 * alpha + r2 * (1 - alpha)),
        int(g1 * alpha + g2 * (1 - alpha)),
        int(b1 * alpha + b2 * (1 - alpha)),
    )


# ── Reusable widgets ──────────────────────────────────────────────────────────

class Btn(ctk.CTkButton):
    """Standard filled purple action button."""
    def __init__(self, parent, **kw):
        kw.setdefault("height", 40)
        kw.setdefault("fg_color", C["purple"])
        kw.setdefault("hover_color", C["purple2"])
        super().__init__(parent, corner_radius=8, font=("Segoe UI", 13, "bold"),
                         text_color="#fff", **kw)


class GhostBtn(ctk.CTkButton):
    """Outlined transparent button for secondary actions."""
    def __init__(self, parent, **kw):
        kw.setdefault("height", 40)
        kw.setdefault("border_color", C["border2"])
        kw.setdefault("text_color", C["white"])
        super().__init__(parent, corner_radius=8, font=("Segoe UI", 13, "bold"),
                         fg_color="transparent", border_width=1,
                         hover_color=C["border"], **kw)


class Field(ctk.CTkEntry):
    """Standard dark input field."""
    def __init__(self, parent, **kw):
        kw.setdefault("height", 36)
        super().__init__(parent, corner_radius=6, font=BODY,
                         fg_color=C["card"], border_width=1,
                         border_color=C["border"], text_color=C["white"], **kw)


class Card(ctk.CTkFrame):
    """Dark card panel with a subtle border."""
    def __init__(self, parent, **kw):
        super().__init__(parent, corner_radius=12, fg_color=C["card"],
                         border_width=1, border_color=C["border"], **kw)


class Toast:
    """Temporary status banner."""
    COLORS = {"success": "#10B981", "error": "#EF4444", "warning": "#FBBF24", "info": "#8B5CF6"}
    _current = None  # tracks the active toast frame

    def __init__(self, root, msg, kind="info", ms=3000):
        # Dismiss any toast that's already on screen
        if Toast._current is not None:
            try:
                Toast._current.destroy()
            except Exception:
                pass
            Toast._current = None

        bg = self.COLORS.get(kind, C["purple"])
        frame = ctk.CTkFrame(root, fg_color=bg, corner_radius=8)
        ctk.CTkLabel(frame, text=msg, font=("Segoe UI", 13, "bold"),
                     text_color="#fff").pack(padx=24, pady=12)
        frame.place(relx=0.5, rely=0.05, anchor="n")
        Toast._current = frame
        root.after(ms, lambda: self._dismiss(frame))

    @staticmethod
    def _dismiss(frame):
        try:
            frame.destroy()
            if Toast._current is frame:
                Toast._current = None
        except Exception:
            pass


def _parse_class_name(name):
    nums = re.findall(r"\d+", name)
    std = int(nums[0]) if nums else 10
    section_match = re.search(r"\d+\s*-\s*(.+)$", name)
    if not section_match:
        section_match = re.search(r"\d+\s+([^\d]+)$", name)
    sec = section_match.group(1).strip() if section_match else "A"
    return std, sec


# ── Application ───────────────────────────────────────────────────────────────

class AttendanceProApp(ctk.CTk):

    def __init__(self, db, backend, config):
        super().__init__()
        self.db      = db
        self.bk      = backend
        self.cfg     = config
        self.title(f"{APP} v{VER}")
        self.geometry("1400x900")
        self.configure(fg_color=C["sidebar"])
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self._build()
        self.show_dashboard()

    def _quit(self):
        try:
            self.bk.tts_engine.stop()
        except Exception:
            pass
        plt.close("all")
        self.destroy()
        self.quit()

    # ── Skeleton ──────────────────────────────────────────────────────────────

    def _build(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True)

        # Sidebar — a raw tk.Canvas so we can control z-order of nav buttons
        self.sb = tk.Canvas(wrap, width=240, highlightthickness=0, bg=C["sidebar"])
        self.sb.pack(side="left", fill="y")
        self._build_sidebar()

        # Main content area — pages render here
        self.area = ctk.CTkFrame(wrap, fg_color=C["main"], corner_radius=0)
        self.area.pack(side="right", fill="both", expand=True)

    def _build_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sb, fg_color="transparent")
        self.sb.create_window(120, 75, window=logo_frame, width=200)
        ctk.CTkLabel(logo_frame, text=APP, font=("Segoe UI", 18, "bold"), text_color=C["white"]).pack()
        ctk.CTkLabel(logo_frame, text=f"v{VER}", font=TINY, text_color=C["muted"]).pack()

        # Navigation buttons
        nav_items = [
            ("⊞  Dashboard",  self.show_dashboard,  "Dashboard"),
            ("👥  Students",   self.show_students,   "Students"),
            ("☑  Attendance", self.show_attendance, "Attendance"),
            ("📄  Reports",    self.show_reports,    "Reports"),
            ("🏫  Classes",    self.show_classes,    "Classes"),
            ("⚙  Settings",   self.show_settings,   "Settings"),
        ]
        self.nav_btns = {}
        y = 185
        for label, cmd, key in nav_items:
            btn = ctk.CTkButton(
                self.sb, text=label, font=("Segoe UI", 13, "bold"),
                fg_color="transparent", hover_color=C["card"],
                text_color=C["white"], anchor="w",
                height=44, corner_radius=8, command=cmd,
            )
            self.sb.create_window(120, y, window=btn, width=200, height=44)
            self.nav_btns[key] = btn
            y += 54


    # ── Page helpers ──────────────────────────────────────────────────────────

    def _clear(self):
        """Remove all widgets from the content area."""
        for w in self.area.winfo_children():
            w.destroy()

    def _nav(self, active_key):
        """Highlight the active sidebar button and reset the rest."""
        for key, btn in self.nav_btns.items():
            if key == active_key:
                btn.configure(fg_color=C["purple"], text_color="#fff", hover_color=C["purple2"])
            else:
                btn.configure(fg_color="transparent", text_color=C["white"], hover_color=C["card"])

    def _page(self):
        """Return a fresh frame that fills the content area. Pages manage their own scrolling internally."""
        p = ctk.CTkFrame(self.area, fg_color="transparent", corner_radius=0)
        p.pack(fill="both", expand=True)
        return p

    def _header(self, page, title, subtitle=""):
        """Render a standard page title row and return the header frame."""
        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(30, 20))
        ctk.CTkLabel(hdr, text=title,    font=BIG,  text_color=C["white"]).pack(side="left")
        ctk.CTkLabel(hdr, text=subtitle, font=BODY, text_color=C["muted"]).pack(side="left", padx=15, pady=(8, 0))
        return hdr

    def _form(self, page, title):
        """Return a centred form card for add/edit pages."""
        hdr = ctk.CTkFrame(page, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(30, 20))
        ctk.CTkLabel(hdr, text=title, font=BIG, text_color=C["white"]).pack(side="left")
        card = Card(page)
        card.pack(padx=180, pady=(0, 40), fill="x")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=50, pady=30)
        return inner

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def show_dashboard(self):
        self._clear()
        self._nav("Dashboard")
        page = self._page()

        hdr = self._header(page, "Dashboard", "System overview and daily metrics")

        # Pull live numbers from the database
        total_students  = self.db.get_student_count()
        present_today   = self.db.get_attendance_count_today()
        total_classes   = len(self.db.get_all_classes())
        records_today   = self.db.get_total_attendance_today()
        attendance_pct  = f"{int(present_today / total_students * 100)}% of total" if total_students else "0% of total"

        # Four KPI cards in a row
        kpi_row = ctk.CTkFrame(page, fg_color="transparent")
        kpi_row.pack(fill="x", padx=40, pady=(0, 25))

        kpis = [
            ("👥", C["purple"], str(total_students), "Total Students",  "All registered"),
            ("✅", C["green"],  str(present_today),  "Present Today",   attendance_pct),
            ("🏫", C["blue"],   str(total_classes),  "Total Classes",   "Active classes"),
            ("📄", C["gold"],   str(records_today),  "Records Today",   "Attendance records"),
        ]
        for i, (icon, color, value, title, sub) in enumerate(kpis):
            card = self._kpi_card(kpi_row, icon, color, value, title, sub)
            card.grid(row=0, column=i, padx=(0, 15) if i < 3 else 0, sticky="ew")
            kpi_row.grid_columnconfigure(i, weight=1)

        # Attendance chart
        chart_card = Card(page)
        chart_card.pack(fill="x", padx=40, pady=(0, 40))
        self._draw_chart(chart_card)

    def _kpi_card(self, parent, icon, icon_color, value, title, sub):
        """Build one KPI card: tinted icon box on the left, stats on the right."""
        card = Card(parent, height=95)
        card.pack_propagate(False)

        icon_box = ctk.CTkFrame(card, width=46, height=46, corner_radius=10,
                                fg_color=_tint(icon_color))
        icon_box.pack(side="left", padx=15)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=("Segoe UI", 20),
                     text_color=icon_color).place(relx=0.5, rely=0.5, anchor="center")

        text_col = ctk.CTkFrame(card, fg_color="transparent")
        text_col.pack(side="left", fill="both", expand=True, pady=15)
        ctk.CTkLabel(text_col, text=value, font=("Segoe UI", 24, "bold"), text_color=C["white"]).pack(anchor="w")
        ctk.CTkLabel(text_col, text=title, font=SMALL, text_color=C["muted"]).pack(anchor="w", pady=(2, 0))
        return card

    def _draw_chart(self, parent):
        """Render the attendance trend chart."""
        dates, counts = self.db.get_attendance_last_n_days(7)
        total_students  = self.db.get_student_count()
        x = np.arange(len(dates))
        y = np.array([float(v) for v in counts])

        # Correct average: sum of present / (school days with records × total students)
        # Excludes zero-attendance days (weekends, holidays) from the denominator
        school_days = [v for v in y if v > 0]
        if school_days and total_students:
            avg_pct = (sum(school_days) / (len(school_days) * total_students)) * 100
            avg_str = f"{avg_pct:.1f}%"
        else:
            avg_str = "0%"

        # Chart header row (Average + Weekly Goal card)
        ch = ctk.CTkFrame(parent, fg_color="transparent")
        ch.pack(fill="x", padx=30, pady=(20, 5))

        left = ctk.CTkFrame(ch, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Attendance Overview", font=HEAD, text_color=C["white"]).pack(anchor="w")
        ctk.CTkLabel(left, text="Average attendance",   font=SMALL, text_color=C["muted"]).pack(anchor="w", pady=(12, 0))
        avg_row = ctk.CTkFrame(left, fg_color="transparent")
        avg_row.pack(anchor="w")
        ctk.CTkLabel(avg_row, text=avg_str, font=("Segoe UI", 28, "bold"), text_color=C["purple"]).pack(side="left")
        ctk.CTkLabel(avg_row, text="  last 7 days", font=TINY, text_color=C["muted"]).pack(side="left", pady=(8, 0))

        goal_card = Card(ch)
        goal_card.pack(side="right")
        goal_inner = ctk.CTkFrame(goal_card, fg_color="transparent")
        goal_inner.pack(padx=20, pady=12)
        ctk.CTkLabel(goal_inner, text="📈", font=("Segoe UI", 16), text_color=C["purple"]).pack(side="left", padx=(0, 8))
        goal_text = ctk.CTkFrame(goal_inner, fg_color="transparent")
        goal_text.pack(side="left")
        ctk.CTkLabel(goal_text, text="85%",         font=("Segoe UI", 18, "bold"), text_color=C["purple"]).pack(anchor="w")
        ctk.CTkLabel(goal_text, text="Weekly Goal", font=TINY, text_color=C["muted"]).pack(anchor="w")

        # Matplotlib figure
        bg = C["card"]
        fig, ax = plt.subplots(figsize=(10, 3.0), facecolor=bg)
        ax.set_facecolor(bg)

        if len(x) >= 3:
            xn  = np.linspace(x.min(), x.max(), 300)
            spl = make_interp_spline(x, y, k=min(2, len(x) - 1))
            yn  = np.clip(spl(xn), 0, None)
            ax.fill_between(xn, yn, alpha=0.15, color=C["purple"])
            ax.plot(xn, yn, color=C["purple"], linewidth=2.5)
            ax.scatter([x[-1]], [y[-1]], s=280, color=C["purple"], alpha=0.22)
        elif len(x) > 0:
            ax.plot(x, y, color=C["purple"], linewidth=2.5)

        if len(x) > 0:
            ax.scatter(x, y, s=55, color=C["card"], edgecolors=C["purple"], linewidths=2.0, zorder=4)
            for xi, yi in zip(x, y):
                ax.annotate(str(int(yi)), (xi, yi), textcoords="offset points",
                            xytext=(0, 11), ha="center", fontsize=10,
                            color=C["white"], fontweight="bold")

        # X-axis labels — DB gives "MM/DD", we add day-of-week above
        x_labels = []
        year = datetime.date.today().year
        for d in dates:
            try:
                dt = datetime.datetime.strptime(f"{year}/{d}", "%Y/%m/%d")
                x_labels.append(f"{dt.strftime('%a')}\n{d}")
            except Exception:
                x_labels.append(d)

        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, color=C["muted"], fontsize=9)
        ax.tick_params(colors=C["muted"], length=0)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.yaxis.grid(True, alpha=0.12, color=C["muted"], linestyle="--")
        ax.set_yticks([0, 10, 20, 30, 40])
        ax.set_yticklabels([0, 10, 20, 30, 40], color=C["muted"])
        if len(y): ax.set_ylim(-2, max(45, y.max() * 1.3))
        fig.tight_layout(pad=1.0)

        cv = FigureCanvasTkAgg(fig, parent)
        cv.draw()
        cv.get_tk_widget().pack(fill="x", padx=20, pady=(5, 5))
        plt.close(fig)

        # Legend strip
        leg = ctk.CTkFrame(parent, fg_color="transparent")
        leg.pack(fill="x", padx=30, pady=(0, 18))
        ctk.CTkFrame(leg, width=18, height=2, fg_color=C["purple"]).pack(side="left", pady=(0, 1), padx=(0, 8))
        ctk.CTkLabel(leg, text="This Week",         font=TINY, text_color=C["white"]).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(leg, text="-- --",             font=TINY, text_color=C["purple"]).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(leg, text="No Attendance / No Data", font=TINY, text_color=C["muted"]).pack(side="left")
        ctk.CTkLabel(leg, text="ⓘ Tap a day to view detail", font=TINY, text_color=C["muted"]).pack(side="right")

    # ── Students ──────────────────────────────────────────────────────────────

    def show_students(self):
        self._clear()
        self._nav("Students")
        page = self._page()

        hdr = self._header(page, "Students", "Manage your student roster")
        GhostBtn(hdr, text="Import Data",   width=130, command=self._import_data).pack(side="right")
        Btn(hdr,      text="+ Add Student", width=140, command=self.show_add_student).pack(side="right", padx=(0, 10))

        self.st_query = Field(page, placeholder_text="🔍  Search by name, roll, or GR number")
        self.st_query.pack(fill="x", padx=40, pady=(0, 15))
        self.st_query.bind("<KeyRelease>", lambda e: self._render_students())

        self.st_card = Card(page)
        self.st_card.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self.st_scroll = ctk.CTkScrollableFrame(self.st_card, fg_color="transparent")
        self.st_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._render_students()

    def _render_students(self):
        for w in self.st_scroll.winfo_children():
            w.destroy()
        q = self.st_query.get().strip() if hasattr(self, "st_query") else ""
        students = self.db.get_all_students(q or None)
        if not students:
            ctk.CTkLabel(self.st_scroll, text="No students found.", text_color=C["muted"]).pack(pady=40)
            return
        for sid, grno, rollno, name, std, sec, gen, ph, _ in students[:60]:
            self._student_row(sid, grno, rollno, name, std, sec)

    def _student_row(self, sid, grno, rollno, name, std, sec):
        row = Card(self.st_scroll, height=65)
        row.pack(fill="x", pady=4, padx=5)

        av = ctk.CTkFrame(row, fg_color=C["border"], width=40, height=40, corner_radius=20)
        av.pack(side="left", padx=15, pady=12)
        av.pack_propagate(False)
        ctk.CTkLabel(av, text="👤", text_color=C["muted"]).pack(expand=True)

        ctk.CTkLabel(row, text=name, font=BOLD, text_color=C["white"], width=180, anchor="w").pack(side="left")
        
        info_text = f"Class {std} - {sec}   •   GR No: {grno}   •   Roll No: {rollno}"
        ctk.CTkLabel(row, text=info_text, font=SMALL, text_color=C["muted"], anchor="w").pack(side="left", padx=20)

        GhostBtn(row, text="Delete", width=70, height=30, text_color=C["red"], border_color=C["red"],
                 command=lambda s=sid, n=name: self._del_student(s, n)).pack(side="right", padx=(0, 15))
        GhostBtn(row, text="Edit", width=60, height=30,
                 command=lambda s=sid: self.show_edit_student(s)).pack(side="right", padx=5)

    def show_add_student(self):
        self._clear()
        self._nav("Students")
        page = self._page()
        form = self._form(page, "Add New Student")

        fields = {}
        labels = [("GR Number","grno",0), ("Roll Number","rollno",1),
                  ("Full Name","name",2), ("Gender (M/F)","gender",3), ("Phone Number","phoneno",4)]
        for label, key, row_idx in labels:
            ctk.CTkLabel(form, text=label, font=BOLD, text_color=C["white"]).grid(row=row_idx, column=0, padx=10, pady=10, sticky="w")
            e = Field(form, width=300)
            e.grid(row=row_idx, column=1, padx=10, pady=10)
            fields[key] = e

        ctk.CTkLabel(form, text="Class", font=BOLD, text_color=C["white"]).grid(row=5, column=0, padx=10, pady=10, sticky="w")
        classes = self.db.get_all_classes()
        cnames  = [cl[1] for cl in classes] if classes else ["Default"]
        cls_var = ctk.StringVar(value=cnames[0])
        ctk.CTkComboBox(form, values=cnames, variable=cls_var, width=300,
                        fg_color=C["card"], border_color=C["border"],
                        button_color=C["purple"]).grid(row=5, column=1, padx=10, pady=10)

        def save():
            try:
                g  = fields["grno"].get().strip()
                ro = fields["rollno"].get().strip()
                n  = fields["name"].get().strip()
                ge = fields["gender"].get().strip().upper()
                ph = fields["phoneno"].get().strip()
                for v, lbl in [(g,"GR"),(ro,"Roll"),(n,"Name"),(ge,"Gender"),(ph,"Phone")]:
                    if not v: return Toast(self, f"{lbl} is required", "error")
                if ge not in ("M", "F"): return Toast(self, "Gender must be M or F", "error")
                std, sec = _parse_class_name(cls_var.get())
                cid = self.db.get_class_id_by_name(cls_var.get()) or 1
                sid = self.db.add_student(int(g), int(ro), n, std, sec, ge, ph, cid)
                Toast(self, f"Look at the camera — capturing {n}", "info")
                if self.bk.record_face(n):
                    Toast(self, f"{n} added!", "success")
                else:
                    self.db.delete_student(sid)
                    Toast(self, "Face capture cancelled", "warning")
                self.show_students()
            except Exception as ex:
                Toast(self, str(ex), "error")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=6, column=0, columnspan=2, pady=25)
        Btn(btns,      text="💾 Save & Capture Face", width=220, command=save).pack(side="left", padx=8)
        GhostBtn(btns, text="Cancel", width=110, command=self.show_students).pack(side="left", padx=8)

    def show_edit_student(self, sid):
        student = self.db.get_student_by_id(sid)
        if not student: return Toast(self, "Student not found", "error")

        self._clear()
        self._nav("Students")
        page = self._page()
        form = self._form(page, f"Edit — {student[3]}")

        keys   = ["grno","rollno","name","gender","phoneno"]
        labels = ["GR Number","Roll Number","Full Name","Gender (M/F)","Phone Number"]
        
        # Mapping student tuple: 
        # (id, grno, rollno, name, std, section, gender, phoneno, photo, class_id)
        # 0   1     2       3     4    5        6       7        8      9
        field_indices = {"grno": 1, "rollno": 2, "name": 3, "gender": 6, "phoneno": 7}
        
        fields = {}
        for i, (label, key) in enumerate(zip(labels, keys)):
            ctk.CTkLabel(form, text=label, font=BOLD, text_color=C["white"]).grid(row=i, column=0, padx=10, pady=10, sticky="w")
            e = Field(form, width=300)
            e.insert(0, str(student[field_indices[key]]))
            e.grid(row=i, column=1, padx=10, pady=10)
            fields[key] = e

        ctk.CTkLabel(form, text="Class", font=BOLD, text_color=C["white"]).grid(row=5, column=0, padx=10, pady=10, sticky="w")
        classes = self.db.get_all_classes()
        cnames  = [cl[1] for cl in classes] if classes else ["Default"]
        
        current_class_id = student[9]
        current_class_name = cnames[0]
        for cid, cname in classes:
            if cid == current_class_id:
                current_class_name = cname
                break
                
        cls_var = ctk.StringVar(value=current_class_name)
        ctk.CTkComboBox(form, values=cnames, variable=cls_var, width=300,
                        fg_color=C["card"], border_color=C["border"],
                        button_color=C["purple"]).grid(row=5, column=1, padx=10, pady=10)

        def update():
            try:
                std, sec = _parse_class_name(cls_var.get())
                cid = self.db.get_class_id_by_name(cls_var.get()) or 1
                self.db.update_student(
                    sid,
                    int(fields["grno"].get()),
                    int(fields["rollno"].get()),
                    fields["name"].get().strip(),
                    std,
                    sec,
                    fields["gender"].get().upper().strip(),
                    fields["phoneno"].get().strip(),
                    cid
                )
                Toast(self, "Student updated!", "success")
                self.show_students()
            except Exception as ex:
                Toast(self, str(ex), "error")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=6, column=0, columnspan=2, pady=25)
        Btn(btns,      text="💾 Update Student", width=200, command=update).pack(side="left", padx=8)
        GhostBtn(btns, text="Cancel", width=110, command=self.show_students).pack(side="left", padx=8)

    def _del_student(self, sid, name):
        if messagebox.askyesno("Delete Student", f"Delete {name}?\nThis also removes their face data."):
            self.db.delete_student(sid)
            try:
                self.bk.delete_face_data(name)
            except Exception:
                pass
            Toast(self, f"{name} deleted", "success")
            self._render_students()

    def _import_data(self):
        fp = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not fp: return
        try:
            with open(fp, newline="") as f:
                data = list(csv.DictReader(f))
            n = self.db.bulk_import_students(data)
            Toast(self, f"Imported {n} students", "success")
            self._render_students()
        except Exception as ex:
            Toast(self, str(ex), "error")

    # ── Attendance ────────────────────────────────────────────────────────────

    def show_attendance(self):
        self._clear()
        self._nav("Attendance")
        page = self._page()

        hdr = self._header(page, "Take Attendance", "Face recognition attendance marking")

        # Live stats row
        ts = self.db.get_student_count()
        tp = self.db.get_attendance_count_today()
        kpi_row = ctk.CTkFrame(page, fg_color="transparent")
        kpi_row.pack(fill="x", padx=40, pady=(0, 25))
        for i, (val, label, col) in enumerate([
            (datetime.date.today().strftime("%d %b %Y"), "Today's Date",   C["white"]),
            (str(ts),    "Total Students", C["purple"]),
            (str(tp),    "Present Today",  C["green"]),
            (str(ts-tp), "Yet to Mark",    C["gold"]),
        ]):
            card = Card(kpi_row, height=80)
            card.grid(row=0, column=i, padx=(0, 15) if i < 3 else 0, sticky="ew")
            card.pack_propagate(False)
            kpi_row.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=val,   font=("Segoe UI", 20, "bold"), text_color=col).pack(pady=(16, 2))
            ctk.CTkLabel(card, text=label, font=TINY, text_color=C["muted"]).pack()

        # Action card
        action_card = Card(page)
        action_card.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        centre = ctk.CTkFrame(action_card, fg_color="transparent")
        centre.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(centre, text="📷", font=("Segoe UI", 64)).pack(pady=(0, 15))
        ctk.CTkLabel(centre, text="Ready to Mark Attendance", font=HEAD, text_color=C["white"]).pack(pady=(0, 8))
        ctk.CTkLabel(centre, text="Press Start — the camera opens. Press M to mark, Q to quit.",
                     font=BODY, text_color=C["muted"]).pack(pady=(0, 30))

        def start():
            result = self.bk.recognize_and_mark_attendance(self.db)
            if result is None:
                Toast(self, "No face data found. Add students first.", "warning")
            else:
                try:
                    self.bk.speak("Attendance marked" if result else "No attendance marked")
                except Exception:
                    pass
                Toast(self, "Session complete!", "success")
                self.show_attendance()

        Btn(centre, text="▶  Start Face Recognition", width=250, command=start).pack()

    # ── Reports ───────────────────────────────────────────────────────────────

    def show_reports(self):
        self._clear()
        self._nav("Reports")
        page = self._page()

        hdr = self._header(page, "Reports", "Attendance data and analysis")

        # Filter card
        filter_card = Card(page)
        filter_card.pack(fill="x", padx=40, pady=(0, 20))
        fr = ctk.CTkFrame(filter_card, fg_color="transparent")
        fr.pack(fill="x", padx=20, pady=20)

        # Name
        col1 = ctk.CTkFrame(fr, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(col1, text="Student Name", font=SMALL, text_color=C["white"]).pack(anchor="w", pady=(0, 5))
        self.rep_name = Field(col1, placeholder_text="Search by name")
        self.rep_name.pack(fill="x")

        # From date
        col2 = ctk.CTkFrame(fr, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(col2, text="From", font=SMALL, text_color=C["white"]).pack(anchor="w", pady=(0, 5))
        self.rep_from = Field(col2)
        self.rep_from.insert(0, str(datetime.date.today() - datetime.timedelta(days=30)))
        self.rep_from.pack(fill="x")

        # To date
        col3 = ctk.CTkFrame(fr, fg_color="transparent")
        col3.pack(side="left", fill="x", expand=True, padx=(0, 12))
        ctk.CTkLabel(col3, text="To", font=SMALL, text_color=C["white"]).pack(anchor="w", pady=(0, 5))
        self.rep_to = Field(col3)
        self.rep_to.insert(0, str(datetime.date.today()))
        self.rep_to.pack(fill="x")

        # Action buttons
        btn_col = ctk.CTkFrame(fr, fg_color="transparent")
        btn_col.pack(side="left", padx=(0, 0), pady=(18, 0))
        Btn(btn_col,      text="Generate",   width=110, command=self._gen_report).pack(pady=(0, 8))
        GhostBtn(btn_col, text="⬇ Download", width=110, command=self._dl_report).pack()

        # Results panel
        self.rep_panel = Card(page)
        self.rep_panel.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self._report_placeholder()

    def _report_placeholder(self):
        for w in self.rep_panel.winfo_children(): w.destroy()
        c = ctk.CTkFrame(self.rep_panel, fg_color="transparent")
        c.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(c, text="📋", font=("Segoe UI", 60)).pack(pady=(0, 15))
        ctk.CTkLabel(c, text="Set filters above and press Generate",
                     font=BODY, text_color=C["muted"]).pack()

    def _gen_report(self):
        nm   = self.rep_name.get().strip()
        recs = self.db.get_attendance_reports(
            self.rep_from.get(), self.rep_to.get(), nm or None
        )
        for w in self.rep_panel.winfo_children(): w.destroy()

        top = ctk.CTkFrame(self.rep_panel, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(top, text=f"{len(recs)} record(s) found", font=HEAD, text_color=C["white"]).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self.rep_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not recs:
            ctk.CTkLabel(scroll, text="No records match your filters.", text_color=C["muted"]).pack(pady=40)
            return

        for name, grno, rollno, cls, date, time, status in recs:
            row = Card(scroll, height=60)
            row.pack(fill="x", pady=4, padx=5)
            col = C["green"] if status == "P" else C["red"]
            ctk.CTkFrame(row, fg_color=col, width=4, corner_radius=4).pack(side="left", fill="y")
            ctk.CTkLabel(row, text=name,           font=BOLD,  text_color=C["white"], width=160, anchor="w").pack(side="left", padx=12)
            ctk.CTkLabel(row, text=f"Class {cls}", font=SMALL, text_color=C["muted"], width=80,  anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{date}  {time}", font=SMALL, text_color=C["muted"], width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text="Present" if status == "P" else "Absent",
                         font=BOLD, text_color=col).pack(side="right", padx=20)

    def _dl_report(self):
        nm   = self.rep_name.get().strip() if hasattr(self, "rep_name") else ""
        recs = self.db.get_attendance_reports(
            self.rep_from.get(), self.rep_to.get(), nm or None
        )
        if not recs: return Toast(self, "Nothing to download", "warning")
        fn = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if fn:
            ok = self.bk.export_to_csv(recs, ["Name","GR","Roll","Class","Date","Time","Status"], fn)
            Toast(self, "Downloaded!" if ok else "Export failed", "success" if ok else "error")

    # ── Classes ───────────────────────────────────────────────────────────────

    def show_classes(self):
        self._clear()
        self._nav("Classes")
        page = self._page()

        hdr = self._header(page, "Classes", "Manage class batches")
        Btn(hdr, text="+ Add Class", width=130, command=self._add_class_form).pack(side="right")

        self.cls_wrap = Card(page)
        self.cls_wrap.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self.cls_scroll = ctk.CTkScrollableFrame(self.cls_wrap, fg_color="transparent")
        self.cls_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._render_classes()

    def _render_classes(self):
        for w in self.cls_scroll.winfo_children(): w.destroy()
        classes = self.db.get_classes_detailed()
        if not classes:
            ctk.CTkLabel(self.cls_scroll, text="No classes yet. Create one!",
                         text_color=C["muted"]).pack(pady=40)
            return
        for cid, name, desc, _, count in classes:
            row = Card(self.cls_scroll, height=75)
            row.pack(fill="x", pady=5, padx=5)
            ib = ctk.CTkFrame(row, fg_color=C["border"], width=46, height=46, corner_radius=10)
            ib.pack(side="left", padx=15, pady=15)
            ib.pack_propagate(False)
            ctk.CTkLabel(ib, text="🏫", text_color=C["muted"]).pack(expand=True)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=15)
            ctk.CTkLabel(info, text=name,              font=BOLD,  text_color=C["white"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=desc or "No description", font=SMALL, text_color=C["muted"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(row, text=f"👥 {count}", font=SMALL, text_color=C["muted"]).pack(side="left", padx=15)
            GhostBtn(row, text="Delete", width=75, height=30, text_color=C["red"], border_color=C["red"],
                     command=lambda c=cid, n=name: self._del_class(c, n)).pack(side="right", padx=15)

    def _add_class_form(self):
        for w in self.cls_wrap.winfo_children(): w.destroy()
        c = ctk.CTkFrame(self.cls_wrap, fg_color="transparent")
        c.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(c, text="Add New Class", font=HEAD, text_color=C["white"]).pack(pady=(0, 20))

        row1 = ctk.CTkFrame(c, fg_color="transparent")
        row1.pack(pady=(0, 12))
        ctk.CTkLabel(row1, text="Class  ", font=BOLD, text_color=C["muted"]).pack(side="left")
        self.cls_num_entry = Field(row1, placeholder_text="e.g. 10", width=140)
        self.cls_num_entry.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(row1, text="Section  ", font=BOLD, text_color=C["muted"]).pack(side="left")
        self.cls_sec_entry = Field(row1, placeholder_text="e.g. A", width=80)
        self.cls_sec_entry.pack(side="left")

        self.cls_desc_entry = Field(c, placeholder_text="Description (optional)", width=300)
        self.cls_desc_entry.pack(pady=(0, 20))

        btns = ctk.CTkFrame(c, fg_color="transparent")
        btns.pack()
        Btn(btns,      text="Save",   width=120, command=self._save_class).pack(side="left", padx=5)
        GhostBtn(btns, text="Cancel", width=100, command=self.show_classes).pack(side="left", padx=5)

    def _save_class(self):
        num = self.cls_num_entry.get().strip()
        sec_raw = self.cls_sec_entry.get().strip()
        # Normalize section: uppercase if single character, else capitalize first letter
        sec = sec_raw.upper() if len(sec_raw) == 1 else sec_raw.capitalize()
        if not num: return Toast(self, "Class number is required", "error")
        name = f"Class {num}" + (f" - {sec}" if sec else "")
        try:
            self.db.add_class(name, self.cls_desc_entry.get().strip())
            Toast(self, f"'{name}' created", "success")
            self.show_classes()
        except Exception as ex:
            Toast(self, str(ex), "error")

    def _del_class(self, cid, name):
        if messagebox.askyesno("Delete Class", f"Delete '{name}'?"):
            try:
                self.db.delete_class(cid)
                Toast(self, f"'{name}' deleted", "success")
                self._render_classes()
            except Exception as ex:
                Toast(self, str(ex), "error")

    # ── Settings ──────────────────────────────────────────────────────────────

    def show_settings(self):
        self._clear()
        self._nav("Settings")
        page = self._page()

        hdr = self._header(page, "Settings", "System configuration")

        # Config items
        config_card = Card(page)
        config_card.pack(fill="x", padx=40, pady=(0, 20))
        dbp = getattr(self.db, "DB_PATH", self.cfg.get("db_path", "N/A"))
        items = [
            ("📁  Database",         dbp,                                              "SQLite database file location"),
            ("👤  Face Dataset",      self.cfg.get("dataset_dir", "N/A"),              "Training images directory"),
            ("🎥  Camera Index",      str(self.cfg.get("camera_index", 0)),            "Webcam device index (0 = default)"),
            ("🎯  Match Threshold",   str(self.cfg.get("recognition_threshold", 0.6)), "Face confidence threshold (0–1)"),
        ]
        for title, value, desc in items:
            row = ctk.CTkFrame(config_card, fg_color="transparent")
            row.pack(fill="x", padx=25, pady=14)
            ctk.CTkLabel(row, text=title, font=BOLD,  text_color=C["white"]).pack(anchor="w")
            ctk.CTkLabel(row, text=value, font=SMALL, text_color=C["purple"]).pack(anchor="w", pady=2)
            ctk.CTkLabel(row, text=desc,  font=TINY,  text_color=C["muted"]).pack(anchor="w")
            ctk.CTkFrame(config_card, fg_color=C["border"], height=1).pack(fill="x", padx=25)

        # About
        about = Card(page)
        about.pack(fill="x", padx=40, pady=(0, 40))
        ctk.CTkLabel(about, text=APP, font=("Segoe UI", 18, "bold"), text_color=C["white"]).pack(pady=(24, 4))
        ctk.CTkLabel(about, text=f"v{VER}", font=SMALL, text_color=C["purple"]).pack()
        ctk.CTkLabel(about, text="Face Recognition Attendance System", font=BODY, text_color=C["muted"]).pack(pady=4)
        ctk.CTkLabel(about, text="Built with Python · CustomTkinter · OpenCV · SQLite",
                     font=TINY, text_color=C["muted"]).pack(pady=(0, 24))
