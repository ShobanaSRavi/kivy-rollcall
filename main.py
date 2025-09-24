import bcrypt
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.button import MDFlatButton,MDIconButton,MDRaisedButton
#from kivymd.uix.button.button import theme_text_color_options
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import MDNavigationLayout
from kivymd.uix.toolbar import MDTopAppBar

from kivymd.uix.dialog import MDDialog
#from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.uix.textfield import MDTextField
from rollcall import RollCallScreen
from studentslistscreen import StudentsListScreen
from kivy.properties import StringProperty, NumericProperty, ObjectProperty,BooleanProperty
import sqlite3
from kivy.factory import Factory
from Query import QueryScreen
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup

DB_NAME = "hariom-attendance.db"
Window.size = (360, 640)



class HomeScreen(Screen):
    app = ObjectProperty(None)
    def __init__(self,**kwargs):

        #self.app = app
        #self.nav_drawer = kwargs.pop("nav_drawer", None)
        super().__init__(**kwargs)
        self.dialog = None

    @property
    def app(self):
        return MDApp.get_running_app()



    def show_dialog(self, title, text):
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ],
        )
        self.dialog.open()

    def register_user(self, username, password):
        if not username or not password:
            self.show_dialog("Error", "⚠ Please enter both username and password")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Check if username already exists
            cursor.execute("SELECT * FROM app_users WHERE username=?", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                conn.close()
                self.show_dialog("Already Registered", "⚠ Username already exists. Please log in.")
                return

            # Salt generation + password hashing
            '''hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            # Store as UTF-8 string
            hashed_password_str = hashed_password.decode("utf-8")'''

            cursor.execute(
                "INSERT INTO app_users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            self.show_dialog("Registration Success", "✅ You can now log in.")
            # Clear the text fields after a successful registration
            self.ids.user.text = ""
            self.ids.pwd.text = ""
        except Exception as e:
            self.show_dialog("Error", f"An error occurred: {e}")

    def login(self, username, password):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM app_users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            self.show_dialog("Login Failed", "❌ No user exists. Signup first.")
            return

        # Get the stored hash (string) and convert back to bytes
        '''stored_hashed_password_str = user[2]
        stored_hashed_password = stored_hashed_password_str.encode("utf-8")
        password_bytes = password.encode("utf-8")'''
        stored_password = user[2].strip()
        input_password = password.strip()
        try:
            #if bcrypt.checkpw(password_bytes, stored_hashed_password):
            if stored_password == input_password:
                app = MDApp.get_running_app()
                app.is_logged_in = True
                self.is_logged_in = True
                self.show_dialog("Login Success", f"✅ Welcome {username}!")
                self.manager.current = "home"

                self.app.root.ids.nav_drawer.set_state("open")
                #self.root.ids.screen_manager.current = "home"
                self.manager.current = "home"
                # Clear the text fields
                self.ids.user.text = ""
                self.ids.pwd.text = ""

            else:
                self.show_dialog("Login Failed", "❌ Invalid password.")
        except ValueError as e:
            self.show_dialog("Login Failed", "❌ Invalid password or user data.")

class StudentListRow(MDBoxLayout):
    name = StringProperty()
    age = StringProperty()
    phone = StringProperty()
    checked = BooleanProperty(False)
class StudentRow(MDBoxLayout):
    name = StringProperty()
    #age = StringProperty()
    #phone = StringProperty()
    checked = BooleanProperty(False)
class StudentsListScreen(Screen):
    pass

class RollCallScreen(Screen):
    pass

class QueryScreen(Screen):
    pass
class MainAppRoot(MDNavigationLayout):
    is_logged_in = BooleanProperty(False)
    pass

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Student details table (main source of truth)
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS studentdetails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    age INTEGER,
                    phone TEXT
                )
            """)

    # Attendance table
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS bv_kids (
                Date TEXT,
                Student TEXT,
                Present INTEGER,
                PRIMARY KEY (Date, Student)
            )
        """)

    conn.commit()
    conn.close()



class RollCallApp(MDApp):
    is_logged_in = BooleanProperty(False)
    dialog = None
    students= []

    def build(self):
        init_db()
        print("Attempting to load hariom.kv")
        root = Builder.load_file("hariom.kv")
        print("hariom.kv loaded successfully!")
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette="Blue"
        return root

    def pick_image(self):
        chooser = FileChooserIconView(filters=["*.png", "*.jpg", "*.jpeg"])
        popup = Popup(title="Select Profile Image",
                      content=chooser,
                      size_hint=(0.9, 0.9))

        chooser.bind(on_submit=lambda fc, selection, touch: self.set_profile_image(selection, popup))
        popup.open()

    def set_profile_image(self, selection, popup):
        if selection:
            path = selection[0]  # first selected file
            self.root.ids.profile_img.source = path
            popup.dismiss()

    def check_and_switch(self, screen_name):
        if self.is_logged_in:
            """Change the current screen from navigation menu"""
            self.root.ids.screen_manager.current = screen_name
            self.root.ids.nav_drawer.set_state("close")
        else:
            self.show_error_dialog("You are not logged in!")

    def show_error_dialog(self,message):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Access Denied",
                text=message,
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: self.dialog.dismiss()
                    )
                ],
            )
        else:
            self.dialog.text = message
        self.dialog.open()
    def on_start(self):
        self.load_students()

    def load_students(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, age, phone FROM studentdetails")

        self.students = [row[0] for row in cur.fetchall()] #for storing only names
        conn.close()
        print("inserted students:",self.students)

    def logout(self):
        self.is_logged_in = False
        self.root.ids.screen_manager.current = "home"
        self.root.ids.nav_drawer.set_state("close")
        self.root.is_logged_in = False
        # Get the HomeScreen instance from the ScreenManager
        home_screen = self.root.ids.screen_manager.get_screen("home")

        # Clear the text fields on that specific screen
        if hasattr(home_screen.ids, 'user'):
            home_screen.ids.user.text = ""
        if hasattr(home_screen.ids, 'pwd'):
            home_screen.ids.pwd.text = ""

    '''try:
        print("Attempting to load hariom.kv")
        root=Builder.load_file("hariom.kv")
        print("hariom.kv loaded successfully!")
    except Exception as e:
        print(f"Error loading KV file: {e}")
        root=None'''



if __name__ == '__main__':
    RollCallApp().run()
