from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button.button import theme_text_color_options
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock
#from kivymd.app import MDApp
from kivymd.uix.screen import Screen
#from kivymd.uix.scrollview import MDScrollView
#from kivymd.uix.list import MDList
from kivy.uix.screenmanager import Screen
from kivymd.uix.gridlayout import MDGridLayout
from datetime import datetime,date
from kivy.app import App
from kivymd.uix.pickers import MDDatePicker
import sqlite3
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton,MDIconButton
import os
DB_NAME = "hariom-attendance.db"
class StudentRow(MDBoxLayout):
    student_name = StringProperty()

    today_date = datetime.now().strftime("%B %d, %Y")
    name = StringProperty("")
    present = BooleanProperty(False)
    age = StringProperty("")
    phone = StringProperty("")
    checked = BooleanProperty(False)
    controller = ObjectProperty(None)
    def on_checkbox_active(self, checkbox, value):
        self.present =  value
        if self.controller:  # checked
            print(f"Checkbox selected for {self.name}")
            self.controller.on_present_toggle(self.student_name, value)
class RollCallScreen(Screen):
    app = ObjectProperty(None)
    
    def __init__(self,**kwargs):
        #self.app = app
        super().__init__(**kwargs)
        #self.app = app
        #self.app = App.get_running_app()
        #self.selected_students = []

    @property
    def app(self):
        return MDApp.get_running_app()


    def on_pre_enter(self, *args):
        #self.app.load_students()
        self.populate_students()
        self.display_current_date()

    def on_present_toggle(self, student_name, active_state):
        """
        Updates the 'present' status in the RecycleView's data list.
        """
        # Iterate through the data list of the RecycleView
        for student_dict in self.ids.student_rv_rollcall.data:
            # Find the dictionary for the student whose checkbox was toggled
            if student_dict['student_name'] == student_name:
                # Update the 'present' status with the new active_state
                student_dict['present'] = active_state
                print(f"Attendance for {student_name} updated to Present: {active_state}")
                # Stop searching once the student is found
                #return
                break

    def display_current_date(self):
        today = datetime.now().strftime("%m/%d/%Y")

        self.ids.date_label.text = today


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
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        """When user selects a date, update label."""
        if "date_label" in self.ids:
            self.ids.date_label.text = value.strftime("%m/%d/%Y")
            print(f"Date selected: {value}")
        else:
            print("date_label not found in self.ids")
        
        
    def populate_students(self):

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hariom-attendance.db")
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT name FROM studentdetails")
            students = cursor.fetchall()

        self.ids.student_rv_rollcall.data = [
            {"student_name": name, "present": False, "controller": self}
            for (name,) in students
        ]
        #self.selected_students.clear()

    def submit_attendance(self):
        date = self.ids.date_label.text if self.ids.date_label.text != "Pick a date" \
            else datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Create table if not exists
        cur.execute('''CREATE TABLE IF NOT EXISTS bv_kids (
        Date TEXT,
        Student TEXT,
        Present Text,
        PRIMARY KEY (Date, Student)
        )''')

    # Loop over the data list of the RecycleView

        for student_dict in self.ids.student_rv_rollcall.data:
            student_name = student_dict['student_name']

            # The 'present' key holds the boolean status of the checkbox
            present_status = 1 if student_dict.get('present', False) else 0

            cur.execute('''INSERT OR REPLACE INTO bv_kids (Date, Student, Present)
                                               VALUES (?, ?, ?)''',
                        (date, student_name, present_status))
        conn.commit()
        conn.close()
        print(f"Attendance saved for {date} ")

        #  Clearing checkboxes after submit

        for row in self.ids.student_rv_rollcall.data:
            print(row["student_name"],row["present"])

        for i in range(len(self.ids.student_rv_rollcall.data)):
            self.ids.student_rv_rollcall.data[i]["present"] = False

        # Trigger refresh of RecycleView
        self.ids.student_rv_rollcall.refresh_from_data()






