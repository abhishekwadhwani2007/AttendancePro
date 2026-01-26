import customtkinter as ctk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog
import datetime
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

THEME = {
    # Backgrounds
    "bg_primary": "#0F0F1A",
    "bg_secondary": "#1A1B26",
    "bg_tertiary": "#24253A",
    "card_bg": "#2A2B3E",
    "card_hover": "#353649",
    # Accent Colors
    "accent_purple": "#5865F2",
    "accent_blue": "#00D9FF",
    "accent_pink": "#FF6B9D",
    "accent_yellow": "#FFC700",
    # Status Colors
    "success": "#3BA55D",
    "warning": "#FAA81A",
    "danger": "#ED4245",
    "info": "#7289DA",
    # Text
    "text_primary": "#FFFFFF",
    "text_secondary": "#B9BBBE",
    "text_tertiary": "#72767D",
    # Borders
    "border": "#3A3B4E",
    "border_focus": "#5865F2",
}

APP_NAME = "AttendancePro"
VERSION = "2.0"

class Toast:
    def __init__(self, parent, message, type="info", duration=3000):
        self.toast = ctk.CTkFrame(
            parent,
            fg_color=THEME["success"] if type == "success" else THEME["danger"] if type == "error" else THEME["warning"] if type == "warning" else THEME["info"],
            corner_radius=10
        )
        
        icon_map = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        
        icon = icon_map.get(type, "ℹ")
        ctk.CTkLabel(
            self.toast,
            text=f"{icon} {message}",
            font=("Segoe UI", 14, "bold"),
            text_color="#FFFFFF"
        ).pack(padx=20, pady=12)
        
        self.toast.place(relx=0.5, rely=0.05, anchor="n")
        parent.after(duration, self.destroy)
    
    def destroy(self):
        self.toast.destroy()

class ModernButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        defaults = {
            "corner_radius": 10,
            "font": ("Segoe UI", 14, "bold"),
            "height": 45,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

class ModernEntry(ctk.CTkEntry):
    def __init__(self, master, **kwargs):
        defaults = {
            "corner_radius": 8,
            "font": ("Segoe UI", 14),
            "height": 40,
            "border_width": 2,
            "fg_color": THEME["card_bg"],
            "border_color": THEME["border"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

class ModernCard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        defaults = {
            "corner_radius": 15,
            "fg_color": THEME["card_bg"],
            "border_width": 1,
            "border_color": THEME["border"],
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

class AttendanceProApp(ctk.CTk):
    
    def __init__(self, db_module, backend_module, config):
        super().__init__()
        
        # Store modules
        self.db = db_module
        self.backend = backend_module
        self.config = config
        
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1400x900")
        self.configure(fg_color=THEME["bg_primary"])
        
        # State
        self.current_view = None
        # Create main layout
        self.create_layout()
        # Show dashboard
        self.show_dashboard()
    
    def create_layout(self):
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        self.create_sidebar()
        self.content_area = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_secondary"],
            corner_radius=0
        )
        self.content_area.pack(side="right", fill="both", expand=True)
    
    def create_sidebar(self):
        sidebar = ctk.CTkFrame(
            self.main_container,
            width=280,
            fg_color=THEME["bg_tertiary"],
            corner_radius=0
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False) #Prevents the frame from shrinking to fit its content, keeping the fixed width
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", pady=20, padx=20)
        ctk.CTkLabel(
            logo_frame,
            text=APP_NAME,
            font=("Segoe UI", 24, "bold"),
            text_color=THEME["accent_purple"]
        ).pack()
        ctk.CTkLabel(
            logo_frame,
            text=f"v{VERSION}",
            font=("Segoe UI", 11),
            text_color=THEME["text_tertiary"]
        ).pack()
        
        nav_buttons = [
            ("📊", "Dashboard", self.show_dashboard, THEME["accent_purple"]),
            ("👥", "Students", self.show_students, THEME["accent_blue"]),
            ("✓", "Attendance", self.show_attendance, THEME["accent_pink"]),
            ("📈", "Reports", self.show_reports, THEME["accent_yellow"]),
            ("📚", "Classes", self.show_classes, THEME["info"]),
            ("⚙", "Settings", self.show_settings, THEME["text_secondary"]),
        ]
        
        self.nav_buttons = {}
        for icon, text, command, color in nav_buttons:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {text}",
                font=("Segoe UI", 15, "bold"),
                fg_color="transparent",
                hover_color=THEME["card_hover"],
                text_color=THEME["text_secondary"],
                anchor="w",
                height=50,
                command=command
            )
            btn.pack(fill="x", padx=15, pady=5)
            self.nav_buttons[text] = btn
    
    def clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def set_active_nav(self, name):
        for btn_name, btn in self.nav_buttons.items():
            if btn_name == name:
                btn.configure(fg_color=THEME["card_bg"], text_color=THEME["text_primary"])
            else:
                btn.configure(fg_color="transparent", text_color=THEME["text_secondary"])
    
    def show_dashboard(self):
        self.clear_content()
        self.set_active_nav("Dashboard")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="📊 Dashboard",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Stats cards
        stats_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=10)
        
        # Get stats
        total_students = self.db.get_student_count()
        today_present = self.db.get_attendance_count_today()
        total_classes = len(self.db.get_all_classes())
        total_attendance_today = self.db.get_total_attendance_today()
        
        stats = [
            ("Total Students", str(total_students), THEME["accent_purple"], "👥"),
            ("Present Today", str(today_present), THEME["success"], "✓"),
            ("Total Classes", str(total_classes), THEME["accent_blue"], "📚"),
            ("Attendance Today", str(total_attendance_today), THEME["accent_pink"], "📝"),
        ]
        
        for i, (title, value, color, icon) in enumerate(stats): #To keep track with index number
            card = ModernCard(stats_frame)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            stats_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 40)).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=value, font=("Segoe UI", 36, "bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 14), text_color=THEME["text_secondary"]).pack(pady=(0, 20))
        
        # Charts section
        charts_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Search filter for attendance trends
        filter_frame = ctk.CTkFrame(charts_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        self.dashboard_trend_name = ModernEntry(
            filter_frame,
            placeholder_text="🔍 Search attendance trends by student name (leave blank for overall)...",
            width=450,
        )
        self.dashboard_trend_name.pack(side="left", padx=(0, 10))
        
        ModernButton(
            filter_frame,
            text="Apply Filter",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=self.load_dashboard_trend_chart,
            width=120,
            height=40,
        ).pack(side="left")
        
        # Container for the chart (will be redrawn on filter)
        self.dashboard_trend_container = ctk.CTkFrame(charts_frame, fg_color="transparent")
        self.dashboard_trend_container.pack(fill="both", expand=True, pady=(0, 10))
        
        # Initial chart load
        dates, counts = self.db.get_attendance_last_n_days(7)
        self.create_attendance_chart(
            self.dashboard_trend_container,
            title="Attendance Trends - Overall (Last 7 Days)",
            dates=dates,
            counts=counts
        )
        
        # Recent activity
        self.create_recent_activity(charts_frame)
    
    def load_dashboard_trend_chart(self):
        # Clear existing chart
        for widget in self.dashboard_trend_container.winfo_children():
            widget.destroy()
        
        name = self.dashboard_trend_name.get().strip()
        
        if name:
            dates, counts = self.db.get_attendance_trend_by_name(name, 7)
            if not dates or sum(counts) == 0:
                Toast(self, f"No attendance data found for '{name}'", "info")
                dates, counts = self.db.get_attendance_last_n_days(7)
                title = "Attendance Trends - Overall (Last 7 Days)"
            else:
                title = f"Attendance Trends - {name} (Last 7 Days)"
        else:
            dates, counts = self.db.get_attendance_last_n_days(7)
            title = "Attendance Trends - Overall (Last 7 Days)"
        
        self.create_attendance_chart(
            self.dashboard_trend_container,
            title=title,
            dates=dates,
            counts=counts
        )
    
    def create_attendance_chart(self, parent, title="Attendance Trends (Last 7 Days)", dates=None, counts=None):
        chart_card = ModernCard(parent)
        chart_card.pack(fill="both", expand=True, pady=(0, 10))
        
        ctk.CTkLabel(
            chart_card,
            text=title,
            font=("Segoe UI", 18, "bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=15, padx=20, anchor="w")
        
        # Get data if not provided
        if dates is None or counts is None:
            dates, counts = self.db.get_attendance_last_n_days(7)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 4), facecolor=THEME["card_bg"])
        ax.set_facecolor(THEME["card_bg"])
        ax.plot(dates, counts, color=THEME["accent_purple"], linewidth=3, marker='o', markersize=8)
        ax.fill_between(dates, counts, alpha=0.3, color=THEME["accent_purple"])
        ax.set_xlabel("Date", color=THEME["text_secondary"], fontsize=12)
        ax.set_ylabel("Students Present", color=THEME["text_secondary"], fontsize=12)
        ax.tick_params(colors=THEME["text_secondary"])
        ax.spines['bottom'].set_color(THEME["border"])
        ax.spines['left'].set_color(THEME["border"])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color=THEME["border"])
        
        canvas = FigureCanvasTkAgg(fig, chart_card)
        canvas.draw() # Renders the matplotlib figure onto the Tkinter canvas
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def create_recent_activity(self, parent):
        activity_card = ModernCard(parent)
        activity_card.pack(fill="x")
        
        ctk.CTkLabel(
            activity_card,
            text="Recent Activity",
            font=("Segoe UI", 18, "bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=15, padx=20, anchor="w")
        
        # Get recent attendance
        records = self.db.get_recent_attendance(5)
        
        if records:
            for name, date, time, status in records:
                item = ctk.CTkFrame(activity_card, fg_color=THEME["bg_tertiary"], height=50)
                item.pack(fill="x", padx=20, pady=5)
                
                status_color = THEME["success"] if status == "P" else THEME["danger"]
                status_text = "Present" if status == "P" else "Absent"
                
                ctk.CTkLabel(
                    item,
                    text=f"👤 {name}",
                    font=("Segoe UI", 14, "bold"),
                    text_color=THEME["text_primary"]
                ).pack(side="left", padx=15, pady=10)
                
                ctk.CTkLabel(
                    item,
                    text=status_text,
                    font=("Segoe UI", 12, "bold"),
                    text_color=status_color
                ).pack(side="right", padx=15)
                
                ctk.CTkLabel(
                    item,
                    text=f"{date} {time}",
                    font=("Segoe UI", 11),
                    text_color=THEME["text_tertiary"]
                ).pack(side="right", padx=10)
        else:
            ctk.CTkLabel(
                activity_card,
                text="No recent activity",
                font=("Segoe UI", 14),
                text_color=THEME["text_tertiary"]
            ).pack(pady=20)
    
    def show_students(self):
        self.clear_content()
        self.set_active_nav("Students")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="👥 Student Management",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ModernButton(
            btn_frame,
            text="➕ Add Student",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=self.show_add_student_inline
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="📥 Bulk Import",
            fg_color=THEME["accent_blue"],
            hover_color=THEME["accent_purple"],
            command=self.bulk_import_dialog
        ).pack(side="left", padx=5)
        
        # Search bar
        search_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=10)
        
        self.student_search = ModernEntry(
            search_frame,
            placeholder_text="🔍 Search students by name, roll no, or GR no..."
        )
        self.student_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.student_search.bind("<KeyRelease>", lambda e: self.load_students()) # Using lambda to defer the function call
        
        # Students list
        list_frame = ModernCard(self.content_area)
        list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Scrollable frame
        self.students_container = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.students_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_students()
    
    def load_students(self):
        # Clear existing
        for widget in self.students_container.winfo_children():
            widget.destroy()
        
        # Get search term
        search = self.student_search.get().lower() if hasattr(self, 'student_search') else ""
        
        # Load students
        students = self.db.get_all_students(search if search else None)
        
        if not students:
            ctk.CTkLabel(
                self.students_container,
                text="No students found",
                font=("Segoe UI", 16),
                text_color=THEME["text_tertiary"]
            ).pack(pady=40)
            return
        
        # Display students
        for student in students:
            self.create_student_card(student)
    
    def create_student_card(self, student):
        sid, grno, rollno, name, std, section, gender, phoneno, photopath = student
        
        card = ctk.CTkFrame(
            self.students_container,
            fg_color=THEME["card_bg"],
            corner_radius=12,
            height=100
        )
        card.pack(fill="x", pady=5)
        
        # Photo
        photo_frame = ctk.CTkFrame(card, fg_color=THEME["bg_tertiary"], width=80, height=80, corner_radius=10)
        photo_frame.pack(side="left", padx=15, pady=10)
        photo_frame.pack_propagate(False)
        ctk.CTkLabel(
            photo_frame,
            text="👤" if gender != "F" else "👩",
            font=("Segoe UI", 36)
        ).pack(expand=True)
        
        # Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=name,
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=f"GR: {grno} | Roll: {rollno} | Class: {std}-{section} | {gender} | {phoneno}",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=2)
        
        # Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=15)
        
        ModernButton(
            actions,
            text="✏ Edit",
            width=80,
            height=35,
            fg_color=THEME["info"],
            command=lambda: self.edit_student_dialog(sid)
        ).pack(side="left", padx=5)
        
        ModernButton(
            actions,
            text="🗑 Delete",
            width=80,
            height=35,
            fg_color=THEME["danger"],
            command=lambda: self.delete_student(sid, name)
        ).pack(side="left", padx=5)
    
    def show_add_student_inline(self):
        self.clear_content()
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="➕ Add New Student",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Center container to constrain width
        center_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        center_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Calculate responsive padding (15% of window width, min 100px)
        window_width = self.winfo_width()
        side_padding = max(100, int(window_width * 0.15))
        
        # Scrollable card with reduced width
        scroll_container = ModernCard(center_container)
        scroll_container.pack(fill="both", expand=True, padx=side_padding, pady=0)
        
        scroll_frame = ctk.CTkScrollableFrame(scroll_container, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        form_card = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        form_card.pack(fill="both", expand=True, padx=20, pady=20)
        
        fields = {}
        
        def add_field(label_text, key, row):
            ctk.CTkLabel(
                form_card,
                text=label_text,
                font=("Segoe UI", 14, "bold"),
                text_color=THEME["text_primary"],
            ).grid(row=row, column=0, padx=10, pady=15, sticky="w")
            
            # Reduced width from 400 to 280 (30% reduction)
            entry = ModernEntry(form_card, width=280)
            entry.grid(row=row, column=1, padx=10, pady=15, sticky="w")
            fields[key] = entry
        
        # All form fields
        add_field("GR Number", "grno", 0)
        add_field("Roll Number", "rollno", 1)
        add_field("Full Name", "name", 2)
        add_field("Standard (Class)", "std", 3)
        add_field("Section", "section", 4)
        add_field("Gender (M/F)", "gender", 5)
        add_field("Phone Number", "phoneno", 6)
        
        # Class dropdown
        ctk.CTkLabel(
            form_card,
            text="Class/Batch",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["text_primary"],
        ).grid(row=7, column=0, padx=10, pady=15, sticky="w")
        
        classes = self.db.get_all_classes()
        classnames = [c[1] for c in classes] if classes else ["Default Class"]
        classvar = ctk.StringVar(value=classnames[0])
        
        class_dropdown = ctk.CTkComboBox(
            form_card,
            values=classnames,
            variable=classvar,
            width=280,
            state="readonly",
            fg_color=THEME["card_bg"],
            button_color=THEME["accent_purple"],
            button_hover_color=THEME["accent_blue"],
        )
        class_dropdown.grid(row=7, column=1, padx=10, pady=15, sticky="w")
        
        # Button frame
        btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=30, sticky="ew")
        
        def save_student():
            try:
                # Get all field values
                grno = fields["grno"].get().strip()
                rollno = fields["rollno"].get().strip()
                name = fields["name"].get().strip()
                std = fields["std"].get().strip()
                section = fields["section"].get().strip().upper()
                gender = fields["gender"].get().strip().upper()
                phoneno = fields["phoneno"].get().strip()  # ← FIXED: was self.phone_entry
                
                # ====== VALIDATION (Bug 6 Fix) ======
                
                # Check empty fields
                if not grno:
                    Toast(self, "❌ GR Number is required", "error")
                    return
                
                if not rollno:
                    Toast(self, "❌ Roll Number is required", "error")
                    return
                
                if not name:
                    Toast(self, "❌ Student Name is required", "error")
                    return
                
                if not std:
                    Toast(self, "❌ Standard/Class is required", "error")
                    return
                
                if not section:
                    Toast(self, "❌ Section is required", "error")
                    return
                
                if not gender:
                    Toast(self, "❌ Gender is required", "error")
                    return
                
                if not phoneno:
                    Toast(self, "❌ Phone Number is required", "error")
                    return
                
                # Validate number formats
                if not grno.isdigit():
                    Toast(self, "❌ GR Number must contain only digits", "error")
                    return
                
                if not rollno.isdigit():
                    Toast(self, "❌ Roll Number must contain only digits", "error")
                    return
                
                if not std.isdigit():
                    Toast(self, "❌ Standard must be a number", "error")
                    return
                
                # Validate gender
                if gender not in ['M', 'F']:
                    Toast(self, "❌ Gender must be M (Male) or F (Female)", "error")
                    return
                
                # Validate phone number
                phone_digits = ''.join(filter(str.isdigit, phoneno))
                if len(phone_digits) != 10:
                    Toast(self, "❌ Phone number must be 10 digits", "error")
                    return
                
                # ====== END VALIDATION ======
                
                # Convert to proper types
                grno = int(grno)
                rollno = int(rollno)
                std = int(std)
                
                # Get class ID
                classid = self.db.get_class_id_by_name(classvar.get())
                if not classid:
                    classid = 1  # Default class fallback
                
                # Add student to database
                self.db.add_student(grno, rollno, name, std, section, gender, phoneno, classid)
                
                # Record face
                Toast(self, f"Recording face for {name}. Look at the camera!", "info")
                success = self.backend.record_face(name)
                
                if success:
                    Toast(self, f"✓ Student {name} added successfully!", "success")
                    self.show_students()
                else:
                    Toast(self, "⚠ Student added but face recording failed", "warning")
                    self.show_students()
                    
            except ValueError as e:
                Toast(self, f"❌ Invalid number format: {str(e)}", "error")
            except Exception as e:
                Toast(self, f"❌ Error: {str(e)}", "error")
        
        ModernButton(
            btn_frame,
            text="💾 Save & Capture Face",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=save_student,
            width=200,
            height=50,
        ).pack(side="right", padx=10)
        
        ModernButton(
            btn_frame,
            text="Cancel",
            fg_color=THEME["card_bg"],
            hover_color=THEME["card_hover"],
            command=self.show_students,
            width=120,
            height=50,
        ).pack(side="right", padx=10)

    def edit_student_dialog(self, student_id):
            """Show edit student interface inline (replaces current view)."""
            student = self.db.get_student_by_id(student_id)
            if not student:
                Toast(self, "Student not found!", "error")
                return
                
            # Clear the main content area to show this form inline
            self.clear_content()
            
            # Header
            header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
            header.pack(fill="x", padx=30, pady=20)
            ctk.CTkLabel(
                header,
                text=f"✏ Edit Student: {student[3]}",
                font=("Segoe UI", 32, "bold"),
                text_color=THEME["text_primary"],
            ).pack(side="left")

            # Center container for responsive width (similar to Add Student)
            center_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
            center_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
            
            # Calculate responsive padding
            window_width = self.winfo_width()
            side_padding = max(100, int(window_width * 0.15))

            # Main Scrollable Card
            scroll_container = ModernCard(center_container)
            scroll_container.pack(fill="both", expand=True, padx=side_padding, pady=0)
            
            scroll_frame = ctk.CTkScrollableFrame(scroll_container, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            form_card = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            form_card.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Prepare Data
            fields = {}
            data = {
                "grno": student[1],
                "rollno": student[2],
                "name": student[3],
                "std": student[4],
                "section": student[5],
                "gender": student[6],
                "phoneno": student[7],
            }
            
            labels = [
                ("GR Number", "grno"),
                ("Roll Number", "rollno"),
                ("Full Name", "name"),
                ("Standard", "std"),
                ("Section", "section"),
                ("Gender (M/F)", "gender"),
                ("Phone Number", "phoneno"),
            ]
            
            # Generate Fields
            for i, (label, key) in enumerate(labels):
                ctk.CTkLabel(
                    form_card,
                    text=label,
                    font=("Segoe UI", 14, "bold"),
                    text_color=THEME["text_primary"],
                ).grid(row=i, column=0, padx=10, pady=15, sticky="w")
                
                entry = ModernEntry(form_card, width=280)
                entry.insert(0, str(data[key]))
                entry.grid(row=i, column=1, padx=10, pady=15, sticky="w")
                fields[key] = entry
                
            # Button frame
            btn_frame = ctk.CTkFrame(form_card, fg_color="transparent")
            btn_frame.grid(row=len(labels)+1, column=0, columnspan=2, pady=30, sticky="ew")
            
            def update_student():
                try:
                    # Basic validation
                    if not fields["name"].get().strip():
                        Toast(self, "Name is required!", "error")
                        return

                    self.db.update_student(
                        student_id,
                        int(fields["grno"].get()),
                        int(fields["rollno"].get()),
                        fields["name"].get().strip(),
                        int(fields["std"].get()),
                        fields["section"].get().upper().strip(),
                        fields["gender"].get().upper().strip(),
                        fields["phoneno"].get().strip()
                    )
                    Toast(self, "Student updated successfully!", "success")
                    # Return to student list
                    self.show_students()
                except ValueError:
                    Toast(self, "Invalid number format in fields!", "error")
                except Exception as e:
                    Toast(self, f"Error: {str(e)}", "error")
            
            def cancel():
                self.show_students()
            
            ModernButton(
                btn_frame,
                text="💾 Update Student",
                fg_color=THEME["accent_purple"],
                hover_color=THEME["accent_blue"],
                command=update_student,
                width=200,
                height=50,
            ).pack(side="right", padx=10)
            
            ModernButton(
                btn_frame,
                text="Cancel",
                fg_color=THEME["card_bg"],
                hover_color=THEME["card_hover"],
                command=cancel,
                width=120,
                height=50,
            ).pack(side="right", padx=10)        
    def delete_student(self, student_id, name):
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {name}?\n\nThis will also delete all attendance records."
        )
        if result:
            try:
                self.db.delete_student(student_id)
                self.backend.delete_face_data(name)
                Toast(self, f"Student {name} deleted successfully!", "success")
                self.load_students()
            except Exception as e:
                Toast(self, f"Error: {str(e)}", "error")
    
    def bulk_import_dialog(self):
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                students_data = list(reader)
            
            count = self.db.bulk_import_students(students_data)
            Toast(self, f"Successfully imported {count} students!", "success")
            self.load_students()
        except Exception as e:
            Toast(self, f"Import error: {str(e)}", "error")
    
    def show_attendance(self):
        self.clear_content()
        self.set_active_nav("Attendance")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="✓ Mark Attendance",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Info cards
        info_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=10)
        
        total = self.db.get_student_count()
        present = self.db.get_attendance_count_today()
        
        stats = [
            ("Date", datetime.date.today().strftime("%B %d, %Y"), THEME["accent_purple"]),
            ("Total Students", str(total), THEME["accent_blue"]),
            ("Present", str(present), THEME["success"]),
            ("Absent", str(total - present), THEME["danger"]),
        ]
        
        for i, (label, value, color) in enumerate(stats):
            card = ModernCard(info_frame)
            card.grid(row=0, column=i, padx=10, sticky="ew")
            info_frame.grid_columnconfigure(i, weight=1)
            
            ctk.CTkLabel(card, text=value, font=("Segoe UI", 28, "bold"), text_color=color).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=label, font=("Segoe UI", 13), text_color=THEME["text_secondary"]).pack(pady=(0, 20))
        
        # Action card
        action_card = ModernCard(self.content_area)
        action_card.pack(fill="both", expand=True, padx=30, pady=(10, 30))
        
        ctk.CTkLabel(
            action_card,
            text="📷 Start Face Recognition",
            font=("Segoe UI", 24, "bold"),
            text_color=THEME["text_primary"],
        ).pack(pady=40)
        
        ctk.CTkLabel(
            action_card,
            text="Click the button below to start marking attendance using face recognition",
            font=("Segoe UI", 14),
            text_color=THEME["text_secondary"],
        ).pack(pady=10)
        
        ModernButton(
            action_card,
            text="🎥 Start Recognition",
            width=250,
            height=60,
            font=("Segoe UI", 18, "bold"),
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=self.start_face_recognition,
        ).pack(pady=30)
        
        ctk.CTkLabel(
            action_card,
            text="Instructions:",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["text_primary"],
        ).pack(pady=(20, 5))
        
        instructions = [
            "• Position your face in front of the camera",
            "• Press 'M' to mark attendance when face is recognized",
            "• Press 'Q' to quit recognition mode",
        ]
        
        for inst in instructions:
            ctk.CTkLabel(
                action_card,
                text=inst,
                font=("Segoe UI", 13),
                text_color=THEME["text_secondary"],
            ).pack(pady=2)
    
    def start_face_recognition(self):
        marked = self.backend.recognize_and_mark_attendance(self.db)
        if marked is None:
            Toast(self, "No face data found! Please add students first.", "warning")
        else:
            # Speak a message when attendance flow ends
            if marked:  # at least one student marked
                self.backend.speak("Attendance marked successfully")
            else:
                self.backend.speak("No attendance was marked")
            Toast(self, "Attendance marking completed!", "success")
            self.show_attendance()
    
    def show_reports(self):
        self.clear_content()
        self.set_active_nav("Reports")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(
            header,
            text="📊 Attendance Reports",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Filters Card
        filter_card = ModernCard(self.content_area)
        filter_card.pack(fill="x", padx=30, pady=(0, 10))
        
        ctk.CTkLabel(
            filter_card,
            text="Filter Options",
            font=("Segoe UI", 18, "bold"),
            text_color=THEME["text_primary"],
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        filter_frame = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # ROW 0: Name filter
        ctk.CTkLabel(
            filter_frame,
            text="Student Name",
            font=("Segoe UI", 13),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.report_name = ModernEntry(filter_frame, placeholder_text="Search by name (optional)", width=250)
        self.report_name.grid(row=0, column=1, padx=10, pady=10, columnspan=2, sticky="ew")
        
        # ROW 1: Date filters
        ctk.CTkLabel(
            filter_frame,
            text="From Date",
            font=("Segoe UI", 13),
            text_color=THEME["text_secondary"],
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.report_from_date = ModernEntry(filter_frame, width=150)
        self.report_from_date.insert(0, str(datetime.date.today() - datetime.timedelta(days=7)))
        self.report_from_date.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(
            filter_frame,
            text="To Date",
            font=("Segoe UI", 13),
            text_color=THEME["text_secondary"],
        ).grid(row=1, column=2, padx=10, pady=10, sticky="w")
        
        self.report_to_date = ModernEntry(filter_frame, width=150)
        self.report_to_date.insert(0, str(datetime.date.today()))
        self.report_to_date.grid(row=1, column=3, padx=10, pady=10, sticky="w")
        
        # Apply button - spanning both rows on the right
        ModernButton(
            filter_frame,
            text="🔍 Apply Filter",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=self.load_reports,
            width=140,
            height=45,
        ).grid(row=0, column=4, rowspan=2, padx=15, pady=10)
        
        # Results Card - MODERNIZED
        results_card = ModernCard(self.content_area)
        results_card.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Header with count
        header_frame = ctk.CTkFrame(results_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📋 Report Results",
            font=("Segoe UI", 20, "bold"),
            text_color=THEME["text_primary"]
        ).pack(side="left")
        
        # Results count badge
        self.results_count_label = ctk.CTkLabel(
            header_frame,
            text="0 records",
            font=("Segoe UI", 12, "bold"),
            text_color=THEME["accent_purple"],
            fg_color=THEME["bg_tertiary"],
            corner_radius=15,
            padx=15,
            pady=5
        )
        self.results_count_label.pack(side="right")
        
        # Scrollable container for results
        self.reports_container = ctk.CTkScrollableFrame(
            results_card,
            fg_color="transparent"
        )
        self.reports_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Export button at bottom
        export_frame = ctk.CTkFrame(results_card, fg_color="transparent")
        export_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ModernButton(
            export_frame,
            text="📥 Download",
            fg_color=THEME["success"],
            command=self.export_reports,
            width=150,
        ).pack(side="right")
        
        # Load initial data
        self.load_reports()
    
        # Load initial data
        self.load_reports()
    
    def load_reports(self):
        # Clear existing
        for widget in self.reports_container.winfo_children():
            widget.destroy()
        
        # Get filter values
        name = self.report_name.get().strip() if hasattr(self, 'report_name') else ""
        from_date = self.report_from_date.get().strip()
        to_date = self.report_to_date.get().strip()
        
        # Fetch records
        try:
            records = self.db.get_attendance_reports(from_date, to_date, f"%{name}%" if name else None)
        except Exception as e:
            Toast(self, f"Error loading reports: {str(e)}", "error")
            return
        
        # Update count
        self.results_count_label.configure(text=f"{len(records)} records")
        
        if not records:
            # Empty state
            empty_frame = ctk.CTkFrame(self.reports_container, fg_color=THEME["bg_tertiary"], corner_radius=12)
            empty_frame.pack(fill="both", expand=True, pady=40, padx=20)
            
            ctk.CTkLabel(
                empty_frame,
                text="📭",
                font=("Segoe UI", 48)
            ).pack(pady=(40, 10))
            
            ctk.CTkLabel(
                empty_frame,
                text="No records found",
                font=("Segoe UI", 18, "bold"),
                text_color=THEME["text_secondary"]
            ).pack(pady=(0, 5))
            
            ctk.CTkLabel(
                empty_frame,
                text="Try adjusting your filters",
                font=("Segoe UI", 13),
                text_color=THEME["text_tertiary"]
            ).pack(pady=(0, 40))
            return
        
        # Display records as modern cards
        for record in records:
            name, grno, rollno, class_section, date, time, status = record
            
            # Create card for each record
            card = ctk.CTkFrame(
                self.reports_container,
                fg_color=THEME["card_bg"],
                corner_radius=10,
                height=80
            )
            card.pack(fill="x", pady=4, padx=5)
            
            # Status indicator (left side colored bar)
            status_color = THEME["success"] if status == "P" else THEME["danger"]
            status_bar = ctk.CTkFrame(card, fg_color=status_color, width=5, corner_radius=10)
            status_bar.pack(side="left", fill="y", padx=(0, 15))
            
            # Content area
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(side="left", fill="both", expand=True, pady=10)
            
            # Name and class (top row)
            top_row = ctk.CTkFrame(content, fg_color="transparent")
            top_row.pack(fill="x", anchor="w")
            
            ctk.CTkLabel(
                top_row,
                text=name,
                font=("Segoe UI", 15, "bold"),
                text_color=THEME["text_primary"],
                anchor="w"
            ).pack(side="left", padx=(0, 15))
            
            ctk.CTkLabel(
                top_row,
                text=f"Class: {class_section}",
                font=("Segoe UI", 12),
                text_color=THEME["accent_blue"],
                fg_color=THEME["bg_tertiary"],
                corner_radius=6,
                padx=10,
                pady=3
            ).pack(side="left")
            
            # Details (bottom row)
            bottom_row = ctk.CTkFrame(content, fg_color="transparent")
            bottom_row.pack(fill="x", anchor="w", pady=(5, 0))
            
            details = [
                ("GR", grno),
                ("Roll", rollno),
                ("Date", date),
                ("Time", time)
            ]
            
            for label, value in details:
                detail_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
                detail_frame.pack(side="left", padx=(0, 20))
                
                ctk.CTkLabel(
                    detail_frame,
                    text=f"{label}: ",
                    font=("Segoe UI", 11),
                    text_color=THEME["text_tertiary"]
                ).pack(side="left")
                
                ctk.CTkLabel(
                    detail_frame,
                    text=str(value),
                    font=("Segoe UI", 11, "bold"),
                    text_color=THEME["text_secondary"]
                ).pack(side="left")
            
            # Status badge (right side)
            status_text = "✓ Present" if status == "P" else "✗ Absent"
            status_label = ctk.CTkLabel(
                card,
                text=status_text,
                font=("Segoe UI", 13, "bold"),
                text_color="white",
                fg_color=status_color,
                corner_radius=8,
                padx=15,
                pady=8
            )
            status_label.pack(side="right", padx=15)
    
    def export_reports(self):
        from_date = self.report_from_date.get().strip()
        to_date = self.report_to_date.get().strip()
        name = self.report_name.get().strip()
        
        records = self.db.get_attendance_reports(
            from_date, to_date, 
            f"%{name}%" if name else None
        )
        
        if not records:
            Toast(self, "No data to export", "warning")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"attendance_{datetime.date.today()}.csv"
        )
        
        if filename:
            success = self.backend.export_to_csv(
                records,
                ["Name", "GR No", "Roll No", "Class", "Date", "Time", "Status"], # column headers
                filename
            )
            if success:
                Toast(self, "Report exported successfully!", "success")
            else:
                Toast(self, "Export failed", "error")

    
    def show_classes(self):
        self.clear_content()
        self.set_active_nav("Classes")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(
            header,
            text="🏫 Class Management",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        ModernButton(
            header,
            text="➕ Add Class",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=self.show_add_class_inline,
        ).pack(side="right")
        
        # List frame
        list_frame = ModernCard(self.content_area)
        list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.classes_list_frame = list_frame
        self.classes_form_frame = None
        
        # Scrollable container
        self.classes_container = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent"
        )
        self.classes_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_classes()

    def load_classes(self):
        for widget in self.classes_container.winfo_children():
            widget.destroy()
        
        classes = self.db.get_classes_detailed()
        
        if not classes:
            ctk.CTkLabel(
                self.classes_container,
                text="No classes found",
                font=("Segoe UI", 16),
                text_color=THEME["text_tertiary"]
            ).pack(pady=40)
            return
        
        for class_data in classes:
            self.create_class_card(class_data)

    def create_class_card(self, class_data):
        cid, name, description, created_at = class_data
        
        # Main card - REMOVE DUPLICATE
        card = ctk.CTkFrame(
            self.classes_container,
            fg_color=THEME["card_bg"],
            corner_radius=12,
            height=100
        )
        card.pack(fill="x", pady=5, padx=5)
        
        # Icon
        icon_frame = ctk.CTkFrame(card, fg_color=THEME["bg_tertiary"], width=80, height=80, corner_radius=10)
        icon_frame.pack(side="left", padx=15, pady=10)
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="🏫", font=("Segoe UI", 36)).pack(expand=True)
        
        # Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=name,
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"],
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=description or "No description",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"],
            anchor="w"
        ).pack(anchor="w", pady=2)
        
        # Actions frame (right side)
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=15)
        
        # Student count
        count = self.db.get_class_student_count(cid)
        ctk.CTkLabel(
            actions,
            text=f"{count} students",
            font=("Segoe UI", 13, "bold"),
            text_color=THEME["accent_blue"],
            fg_color=THEME["bg_tertiary"],
            corner_radius=8,
            padx=12,
            pady=6
        ).pack(pady=5)
        # Delete button was removed in refactor – re-add:
        ModernButton(
                card,
                text="Delete",
                width=80,
                height=35,
                fg_color=THEME["danger"],
                hover_color=THEME["warning"],
                command=lambda c_id=cid, c_name=name: self.delete_class(c_id, c_name),
            ).pack(side="right", padx=10)
            
    def show_add_class_inline(self):
        # Clear content area
        for widget in self.classes_list_frame.winfo_children():
            widget.destroy()
        
        # Create form container
        self.classes_form_frame = ModernCard(self.classes_list_frame)
        self.classes_form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            self.classes_form_frame,
            text="➕ Add New Class",
            font=("Segoe UI", 24, "bold"),
            text_color=THEME["accent_purple"]
        ).pack(pady=(20, 30))
        
        # Form fields
        form_container = ctk.CTkFrame(self.classes_form_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=40)
        
        # Class Name
        ctk.CTkLabel(
            form_container,
            text="Class/Batch Name *",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["text_primary"]
        ).pack(anchor="w", pady=(10, 5))
        
        name_entry = ModernEntry(form_container, placeholder_text="e.g., 10-A, 12-Science, Batch-2025")
        name_entry.pack(fill="x", pady=(0, 20))
        
        # Description
        ctk.CTkLabel(
            form_container,
            text="Description (Optional)",
            font=("Segoe UI", 14, "bold"),
            text_color=THEME["text_primary"]
        ).pack(anchor="w", pady=(10, 5))
        
        desc_entry = ctk.CTkTextbox(
            form_container,
            height=100,
            fg_color=THEME["card_bg"],
            border_width=2,
            border_color=THEME["border"],
            corner_radius=8,
            font=("Segoe UI", 14)
        )
        desc_entry.pack(fill="x", pady=(0, 30))
        
        # Buttons
        btn_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        def save_class():
            name = name_entry.get().strip()
            description = desc_entry.get("1.0", "end-1c").strip()
            
            if not name:
                Toast(self, "Please enter a class name!", "error")
                return
            
            try:
                self.db.add_class(name, description)
                Toast(self, f"Class '{name}' added successfully!", "success")
                self.show_classes()  # Reload the classes view
            except Exception as e:
                Toast(self, f"Error: {str(e)}", "error")
        
        def cancel():
            self.show_classes()
        
        ModernButton(
            btn_frame,
            text="💾 Save Class",
            fg_color=THEME["accent_purple"],
            hover_color=THEME["accent_blue"],
            command=save_class,
            width=160,
            height=45
        ).pack(side="right", padx=5)
        
        ModernButton(
            btn_frame,
            text="✖ Cancel",
            fg_color=THEME["card_bg"],
            hover_color=THEME["card_hover"],
            command=cancel,
            width=120,
            height=45
        ).pack(side="right", padx=5)
        
    def delete_class(self, class_id, name):
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete class {name}?\nThis cannot be undone."
        )
        if not result:
            return
        try:
            self.db.delete_class(class_id)
            Toast(self, f"Class {name} deleted successfully!", "success")
            self.load_classes()
        except Exception as e:
            Toast(self, f"Error: {str(e)}", "error")

    
    def show_settings(self):
        self.clear_content()
        self.set_active_nav("Settings")
        
        # Header
        header = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        header.pack(fill="x", padx=30, pady=20)
        
        ctk.CTkLabel(
            header,
            text="⚙️ Settings",
            font=("Segoe UI", 32, "bold"),
            text_color=THEME["text_primary"],
        ).pack(side="left")
        
        # Settings card
        settings_card = ModernCard(self.content_area)
        settings_card.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # --- BUG FIX 2: Retrieve DB_PATH directly from the imported db module ---
        # We try to get it from self.db.DB_PATH, fallback to config if missing
        actual_db_path = getattr(self.db, 'DB_PATH', self.config.get("db_path", "N/A"))
        
        self.create_setting_item(
            settings_card,
            "📁 Database Path",
            actual_db_path,
            "Location of the attendance database file"
        )
        # ------------------------------------------------------------------------
        
        # Face dataset path
        self.create_setting_item(
            settings_card,
            "👤 Face Dataset Path",
            self.config.get("dataset_dir", "N/A"),
            "Location where face recognition data is stored"
        )
        
        # Camera index
        self.create_setting_item(
            settings_card,
            "🎥 Camera Index",
            str(self.config.get("camera_index", 0)),
            "Camera device index (usually 0 for default camera)"
        )
        
        # Recognition threshold
        self.create_setting_item(
            settings_card,
            "🎯 Recognition Threshold",
            str(self.config.get("recognition_threshold", 0.6)),
            "Confidence threshold for face recognition (0.0 - 1.0)"
        )
        
        # App info
        info_frame = ctk.CTkFrame(settings_card, fg_color=THEME["bg_tertiary"], corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            info_frame,
            text=f"ℹ️ {APP_NAME} v{VERSION}",
            font=("Segoe UI", 16, "bold"),
            text_color=THEME["text_primary"]
        ).pack(pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Modern Face Recognition Attendance System",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"]
        ).pack(pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text="© 2025 AttendancePro. All rights reserved.",
            font=("Segoe UI", 11),
            text_color=THEME["text_tertiary"]
        ).pack(pady=(0, 10))

    def create_setting_item(self, parent, title, value, description):
        item_frame = ctk.CTkFrame(parent, fg_color="transparent")
        item_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            item_frame,
            text=title,
            font=("Segoe UI", 15, "bold"),
            text_color=THEME["text_primary"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            item_frame,
            text=value,
            font=("Segoe UI", 12),
            text_color=THEME["accent_blue"]
        ).pack(anchor="w", pady=2)
        
        ctk.CTkLabel(
            item_frame,
            text=description,
            font=("Segoe UI", 11),
            text_color=THEME["text_tertiary"]
        ).pack(anchor="w")