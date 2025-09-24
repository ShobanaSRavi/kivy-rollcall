from kivy.uix.screenmanager import Screen
#from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp
import sqlite3
import os
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.animation import Animation
import re


def format_phone(phone: str) -> str | None:
    """
    Validate and format phone number as XXX-XXX-XXXX.
    Returns formatted phone if valid, else None.
    """
    # Remove any non-digits
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return None

class StudentsListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.table = None
        self.dialog = None
        self.delete_dialog = None
        self.edit_dialog = None
        self.error_dialog = None  #
        self.selected_students = set()
        self.editing_student_name = None
        self.selected_student_data=None

    def show_error_dialog(self, message: str):
        """Show a popup error dialog with given message."""
        if self.error_dialog:
            self.error_dialog.dismiss()

        self.error_dialog = MDDialog(
            title="Error",
            text=message,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.error_dialog.dismiss()
                )
            ]
        )
        self.error_dialog.open()
    @property
    def app(self):
        return MDApp.get_running_app()

    def on_pre_enter(self):
        # Refresh table whenever the screen is shown
        self.refresh_table()

        # --- Dialog to add student ---
    def create_dialog_content(self):
        box = MDBoxLayout(orientation="vertical", spacing=10, size_hint_y=None, height=200)
        self.student_name_field = MDTextField(hint_text="Name")
        self.student_age_field = MDTextField(hint_text="Age")
        self.student_phone_field = MDTextField(hint_text="Phone number")
        box.add_widget(self.student_name_field)
        box.add_widget(self.student_age_field)
        box.add_widget(self.student_phone_field)
        return box

    def show_add_student_dialog(self, checkbox_instance=None, *args):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Add New Student",
                type="custom",
                content_cls=self.create_dialog_content(),
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: self.dialog.dismiss()),
                    MDFlatButton(text="SAVE", on_release=self.add_student),
                ]
            )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def add_student(self, *args):
        name = self.student_name_field.text.strip().title()
        age = self.student_age_field.text.strip()
        phone = self.student_phone_field.text.strip()

        if not all([name, age, phone]):
            return  # skip if fields empty

        phone_fmt = format_phone(phone)
        if not phone_fmt:
            self.show_error_dialog("❌ Invalid phone number. Enter 10 digits (XXX-XXX-XXXX).")
            return

        # Insert into DB
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hariom-attendance.db")
        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute("""CREATE TABLE IF NOT EXISTS studentdetails (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT,
                                        age INTEGER,
                                        phone TEXT)""")
                cursor.execute("INSERT INTO studentdetails (name, age, phone) VALUES (?, ?, ?)",
                               (name, int(age), phone_fmt))
                db.commit()
        except Exception as e:
            print("DB Error:", e)
            return

        # Clear fields
        self.student_name_field.text = ""
        self.student_age_field.text = ""
        self.student_phone_field.text = ""

        if self.dialog:
            self.dialog.dismiss()

        # Refresh table immediately
        self.refresh_table()
        # --- Checkbox Handling ---
    def toggle_selection(self, name, active):
        if active:
            self.selected_students.add(name)
        else:
            self.selected_students.discard(name)

        if self.selected_students:
            self.show_toolbar()
        else:
            self.hide_toolbar()

    def show_toolbar(self):
        Animation(height=dp(56),opacity=1, d=0.2).start(self.ids.bottom_toolbar)

    def hide_toolbar(self):
        Animation(height=0,opacity=0, d=0.2).start(self.ids.bottom_toolbar)

    def show_delete_dialog(self):
        if not self.selected_students:
            return

        names = ", ".join(self.selected_students)
        self.delete_dialog = MDDialog(
            title="Delete Student(s)?",
            text=f"Do you want to delete: {names} ?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.delete_dialog.dismiss()),
                MDFlatButton(text="DELETE", text_color="red",
                             on_release=lambda x: self.confirm_delete(names)),
            ],
        )
        self.delete_dialog.open()

    def confirm_delete(self, name):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "hariom-attendance.db")
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM studentdetails WHERE name= ?", (name,))
            db.commit()
        """Delete from DB + refresh table"""
        print(f"deleted {name} from db")

        self.selected_students.clear()
        self.hide_toolbar()
        if self.delete_dialog:
            self.delete_dialog.dismiss()
        #self.delete_dialog.dismiss()
        self.refresh_table()

    def on_check_press(self, instance_table, current_row):
        """Called when a checkbox in the table is pressed."""
        # The 'current_row' parameter holds the data for the row that was clicked.
        # It's a tuple like ('Name', 'Age', 'Phone').
        # Store this data to use when the edit button is clicked.
        name,age,phone = current_row

        # Check if the row was selected or deselected
        is_selected = name in self.selected_students

        if not is_selected:
            # Add student to selected set
            self.selected_students.add(name)
        else:
            # Remove student from selected set
            self.selected_students.discard(name)

        if len(self.selected_students) > 0:
            self.show_toolbar()
        else:
            self.hide_toolbar()

    def edit_student_dialog(self):
        """Shows a dialog with the selected student's data for editing."""
        if len(self.selected_students) != 1:
            # Handle cases where 0 or >1 students are selected
            # You can show a popup or a message to the user.
            print("Please select exactly one student to edit.")
            return

        # Get the name of the single selected student
        name_to_edit = list(self.selected_students)[0]

        # 1. Fetch the student's current data from the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hariom-attendance.db")
        student_data = None
        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute("SELECT name, age, phone FROM studentdetails WHERE name=?", (name_to_edit,))
                student_data = cursor.fetchone()
        except Exception as e:
            print("DB Error:", e)
            return

        if not student_data:
            print(f"Error: Could not find student {name_to_edit} in the database.")
            return

        # Store the original name to use in the update query
        self.editing_student_name = name_to_edit

        # 2. Create and populate the dialog fields

        content = self.create_dialog_content()
        self.student_name_field.text = student_data[0]
        self.student_age_field.text = str(student_data[1])
        self.student_phone_field.text = student_data[2]

        self.edit_dialog = MDDialog(
            title=f"Edit {name_to_edit}",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda x: self.edit_dialog.dismiss()),
                MDFlatButton(text="SAVE", on_release=self.update_student),
            ]
        )
        self.edit_dialog.open()

    def update_student(self, *args):
        """Updates the student's record in the database."""
        # Get the new data from the text fields
        new_name = self.student_name_field.text.strip().title()
        new_age = self.student_age_field.text.strip()
        new_phone = self.student_phone_field.text.strip()
        new_phone_fmt = format_phone(new_phone)
        if not new_phone_fmt:
            self.show_error_dialog("❌ Invalid phone number. Enter 10 digits (XXX-XXX-XXXX).")
            return

        # Use the stored original name to find the record to update
        original_name = self.editing_student_name

        new_phone_fmt = format_phone(new_phone)
        if not new_phone_fmt:
            self.show_error_dialog("❌ Invalid phone number. Enter 10 digits (XXX-XXX-XXXX).")
            return

        if not all([new_name, new_age, new_phone]):
            return  # Don't update if fields are empty

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hariom-attendance.db")
        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute("""
                    UPDATE studentdetails 
                    SET name=?, age=?, phone=?
                    WHERE name=?
                """, (new_name, int(new_age), new_phone_fmt, original_name))
                db.commit()
            print(f"Updated student {original_name} to {new_name}.")
        except Exception as e:
            print("DB Error during update:", e)


        if hasattr(self, "edit_dialog") and self.edit_dialog:
            self.edit_dialog.dismiss()

        self.refresh_table()
        # uncheck all checkboxes

        self.selected_students.clear()
        self.hide_toolbar()

    def refresh_table(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hariom-attendance.db")
        students = []
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT name, age, phone FROM studentdetails")
            students = cursor.fetchall()
        # Update RecycleView data
        self.ids.student_rv.data = [{"name": r[0],
                                     "age": str(r[1]),
                                     "phone": r[2],
                                     "active": False
                                     }
                                    for r in students]
        self.selected_students.clear()
        self.hide_toolbar()

