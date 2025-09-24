from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker
from kivymd.app import MDApp
import sqlite3
from datetime import datetime, date

DB_NAME = "hariom-attendance.db"

class QueryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_date = None
        self.selected_student = None
        self.menu = None

    @property
    def app(self):
        return MDApp.get_running_app()

    # --- Date Picker ---
    def open_date_picker(self):

        # Default date: today
        date_dialog = MDDatePicker(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day,
        )
        from kivy.core.window import Window
        w, h = Window.size
        if w < 500:  # Small screen (mobile)
            date_dialog.size_hint = (0.95, 0.9)
        else:  # Tablet/Desktop
            date_dialog.size_hint = (0.6, 0.6)

        date_dialog.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        date_dialog.bind(on_save=self.on_date_selected,
                         on_cancel=self.on_date_cleared)
        date_dialog.open()


    def on_date_selected(self, instance, value, date_range):
        """Callback when a date is picked"""
        self.selected_date = value.strftime("%m/%d/%Y")  # Store the date in the correct format
        self.ids.date_label1.text = value.strftime("%m/%d/%Y")  # Update label with chosen date

    def on_date_cleared(self, *args):
        self.selected_date = None
        self.ids.date_label1.text = "--Select Date--"

    # --- Student Dropdown ---
    def open_student_dropdown(self):
        if not hasattr(self.app, "students") or not self.app.students:
            self.ids.query_result.text = "⚠ No students found. Please add students first."
            return

        menu_items = []
        # one blank space in student list
        menu_items.append({
            "viewclass": "OneLineListItem",
            "text": "— Select Student —",
            "on_release": lambda x=None: self.set_student(None),
        })

        for s in self.app.students:
            if isinstance(s,(tuple,list)) and len(s) >=3:
                text = f"{s[0]} ({s[1]}, {s[2]})"
            else:
                text = str(s)
            menu_items.append({
                "viewclass": "OneLineListItem",
                "text": text,
                "on_release": lambda x=s: self.set_student(x),
            })

        self.menu = MDDropdownMenu(
            caller=self.ids.student_drop_down,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def set_student(self, student_tuple):
        '''self.selected_student = student_tuple
        self.ids.name_label1.text = student_tuple'''
        if student_tuple is None:
            self.selected_student = None
            self.ids.name_label1.text= "--Select Student--"
        else:
            if isinstance(student_tuple, (tuple, list)):
                name = str(student_tuple[0])
            else:
                name = str(student_tuple)
            self.selected_student = name
            self.ids.name_label1.text = name
            if self.menu:
                self.menu.dismiss()

    def submit_query(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        date = self.selected_date
        student = self.selected_student

        # ---------------- CASE 1: Only Date ----------------
        if date and not student:
            cur.execute("SELECT COUNT(*) FROM bv_kids WHERE Date = ? AND Present = ?", (date, "1"))
            count = cur.fetchone()[0]
            if count == 0:
                self.ids.query_result.text = f"There was no class on {date}"
            else:
                cur.execute("SELECT Student FROM bv_kids WHERE Date = ? AND Present = ?", (date, "1"))
                # Fetch all results from the second query.
                students = cur.fetchall()

                # Build a list of names from the fetched tuples.
                student_names = [s[0] for s in students]

                # Join the names into a single string for display.
                students_list_str = "\n ".join(student_names)

                self.ids.query_result.text = f"✅ {count} students were present on {date}\n\nPresent Students:\n\n{students_list_str}"

        # ---------------- CASE 2: Only Student ----------------
        elif student and not date:
            cur.execute("SELECT COUNT(*) FROM bv_kids WHERE Student = ? AND Present = ?", (student, "1"))
            days_present = cur.fetchone()[0]
            cur.execute("SELECT Date FROM bv_kids WHERE Student=? AND Present = ?", (student, "1"))
            dates_present = cur.fetchall()
            dates_list = [d[0] for d in dates_present]
            dates_list_str = "\n ".join(dates_list)
            self.ids.query_result.text = f"✅ {student} was present for {days_present} days\n\nDates {student} was present:\n\n{dates_list_str}"

        # ---------------- CASE 3: Both Date + Student ----------------
        elif student and date:
            cur.execute("SELECT Present FROM bv_kids WHERE Date = ? AND Student = ?", (date, student))
            row = cur.fetchone()
            '''if row is None:
                self.ids.query_result.text = f"❌ {student} was not present on {date}"'''
            if row[0] == 1:
                self.ids.query_result.text = f"✅ {student} was present on {date}"
            else:
                self.ids.query_result.text = f"❌ {student} was absent on {date}"

        # ---------------- CASE 4: Nothing picked ----------------
        else:
            self.ids.query_result.text = "⚠ Please select a date or a student."

        conn.close()
