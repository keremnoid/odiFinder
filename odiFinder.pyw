import requests
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import json
import tkinter as tk
from tkinter import messagebox
import os
import tkinter.font as tkFont
import locale
from typing import Optional, List, Dict, Any, Set
import platform
try:
    from winotify import Notification, audio
    WINOTIFY_AVAILABLE = True
except ImportError:
    WINOTIFY_AVAILABLE = False

try:
    import pystray
    from PIL import Image
    PILLOW_AVAILABLE = True
    PYSTRAY_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    PYSTRAY_AVAILABLE = False
    print("Pillow or pystray library not found. System tray icon will be default. Install with 'pip install pillow pystray'")

locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')

def login_to_odi(username, password):
    """
    Attempts to log in to getodi.com with the given username and password.
    Returns a requests.Session object if successful, otherwise None.
    """
    # You may need to verify the login URL by inspecting the website. (for future updates)
    login_url = "https://getodi.com/sign-in/"
    session = requests.Session()
    login_data = {
        "username": username,
        "password": password
    }
    try:
        response = session.post(login_url, data=login_data)
        if response.status_code == 200:
             # For example, you can check for a text or element that appears after login.
             # Currently, only the status_code is checked, which may not be sufficient.
             print("Login attempt made. Response status code:", response.status_code)
             # A successful login can include a redirect or a specific page check.
             # For example: if "Welcome" in response.text:
             if 'wrong_credentials' in response.url:
                 print("Login failed. Incorrect credentials.")
                 return None
             return session # Assuming login is successful
        else:
            print(f"Login failed. Status code: {response.status_code}")
            return None # Login failed
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during login: {e}")
        return None

def check_meals(session: requests.Session, target_texts: List[str], city_id: str = "35") -> Optional[List[Dict[str, Any]]]:
    """
    Uses the session to check the meals page and search for target texts.
    Returns a list of found meals, including suspended counts, or None if there is an error.
    
    Args:
        session: Active session object
        target_texts: List of restaurant names to search for
        city_id: City ID for filtering meals (default "35" for Izmir)
    """
    import re

    meals_url = f"https://getodi.com/student/?city={city_id}"
    try:
        response = session.get(meals_url)
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            meals_data: List[Dict[str, Any]] = []
            found_meals: Set[str] = set()

            # Find all menu boxes
            menu_boxes = soup.select('div.menu-box')
            for menu_box in menu_boxes:
                if not isinstance(menu_box, Tag):
                    continue

                restaurant_name_tag = menu_box.select_one('div.menu-restaurant')
                menu_title_tag = menu_box.select_one('div.menu-title')
                menu_details_tag = menu_box.select_one('div.menu-details')

                restaurant_name_text = restaurant_name_tag.get_text(strip=True) if restaurant_name_tag else ""
                menu_title_text = menu_title_tag.get_text(strip=True) if menu_title_tag else ""
                menu_details_text = menu_details_tag.get_text(strip=True) if menu_details_tag else ""

                searchable_text_content = f"{restaurant_name_text} {menu_title_text} {menu_details_text}".lower()

                for target_text in target_texts:
                    if target_text.lower() in searchable_text_content and target_text not in found_meals:
                        suspended_count = 0
                        current_price_div = menu_box.select_one('div.current-price')
                        if current_price_div:
                            p_tag = current_price_div.select_one('p')
                            if p_tag:
                                suspended_text = p_tag.get_text(strip=True)
                                match = re.search(r'(\d+)\s*askıda', suspended_text)
                                if match:
                                    try:
                                        suspended_count = int(match.group(1))
                                    except ValueError:
                                        print(f"Could not convert suspended count to int: '{match.group(1)}' for {target_text}")
                        
                        # Determine the display name and description based on the new format
                        # Prioritize menu_title_text for the restaurant name as per the example.
                        actual_restaurant_name_display = menu_title_text
                        if not actual_restaurant_name_display: # If menu_title is empty, use restaurant_name
                            actual_restaurant_name_display = restaurant_name_text
                        if not actual_restaurant_name_display: # If both are empty, fallback to target_text
                            actual_restaurant_name_display = target_text # Ensures name is not empty
                        
                        actual_description = menu_details_text if menu_details_text else "No description available."

                        meal_info = {
                            'name': actual_restaurant_name_display,
                            'description': actual_description, # New key for description
                            'suspended_count': suspended_count,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        meals_data.append(meal_info)
                        found_meals.add(target_text) # Still use target_text to mark this search term as having found something
                        break 
            
            return meals_data
        else:
            print(f"Failed to access the meals page. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking meals: {e}")
        return None
    
def main():
    """
    Main program flow. Loads settings, asks for password, logs in,
    and shows meals in a GUI window with refresh capabilities.
    """
    # Define Theme Colors
    DARK_THEME = {
        "APP_BG": "#2E2E2E",
        "WIDGET_BG": "#3C3C3C", 
        "BUTTON_BG": "#505050",
        "BUTTON_ACTIVE_BG": "#6A6A6A",
        "TEXT_FG": "#E0E0E0",
        "TEXT_AREA_BG": "#1E1E1E",
        "TEXT_AREA_FG": "#D0D0D0",
        "SELECT_BG": "#4A4A4A",
        "BUTTON_TEXT_FG": "#FFFFFF",
        "ENTRY_INSERT_BG": "#E0E0E0"
    }

    LIGHT_THEME = {
        "APP_BG": "#F0F0F0",
        "WIDGET_BG": "#E0E0E0",
        "BUTTON_BG": "#D0D0D0", 
        "BUTTON_ACTIVE_BG": "#B0B0B0",
        "TEXT_FG": "#1E1E1E",
        "TEXT_AREA_BG": "#FFFFFF",
        "TEXT_AREA_FG": "#000000",
        "SELECT_BG": "#C0C0C0",
        "BUTTON_TEXT_FG": "#000000",
        "ENTRY_INSERT_BG": "#000000"
    }
    # Colors for the login window (remains dark themed)
    LOGIN_DARK_COLOR_BG = "#2E2E2E"
    LOGIN_TEXT_AREA_COLOR_BG = "#1E1E1E"
    LOGIN_TEXT_AREA_COLOR_FG = "#D0D0D0"
    LOGIN_TEXT_COLOR_FG = "#E0E0E0"
    LOGIN_BUTTON_COLOR_BG = "#505050"
    LOGIN_BUTTON_TEXT_COLOR_FG = "#FFFFFF"
    LOGIN_BUTTON_COLOR_ACTIVE_BG = "#6A6A6A"


    app_root = None  # Main application window, initialized to None
    periodic_refresh_id = None # ID for the scheduled Tkinter .after job
    previously_found_meal_names = set() # To track meals for notification logic
    current_theme_name = 'dark' # Default theme
    active_colors = DARK_THEME # Initialize with dark theme
    icon_path = None # Will be defined in the try block
    system_tray_icon = None  # Global variable for system tray icon

    PLYER_AVAILABLE = False
    if platform.system() == "Windows":
        if WINOTIFY_AVAILABLE:
            PLYER_AVAILABLE = True
        else:
            print("Winotify library not found. Windows notifications will be disabled. "
                  "Install it with 'pip install winotify'.")
    else:
        try:
            from plyer import notification
            PLYER_AVAILABLE = True
        except ImportError:
            print("Plyer library not found. Notifications will be disabled. "
                  "Install it with 'pip install plyer'.")

    username = ''
    password = ''
    target_texts = ["Rien"]
    notifications_enabled = True
    session = None
    current_city_id = "35" # Default city ID (Izmir)
    city_names = {}  # Dictionary to store city ID to name mappings

    # Load city names from CSV
    try:
        import requests
        import csv
        from io import StringIO
        
        city_csv_url = "https://gist.githubusercontent.com/mebaysan/7a4ba8531187fa8703ff1f22692d5fa6/raw/df4e85262ba2a4f6d6045f06f417b853fb67e78c/il.csv"
        response = requests.get(city_csv_url)
        if response.status_code == 200:
            csv_content = StringIO(response.text)
            csv_reader = csv.reader(csv_content)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                if len(row) >= 2:
                    plate_no = row[0].zfill(2)  # Ensure 2 digits
                    city_name = row[1]
                    city_names[plate_no] = city_name
    except Exception as e:
        print(f"Error loading city names: {e}")
        # Fallback for İzmir if loading fails
        city_names = {"35": "İzmir"}

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, 'odiFinderlogo.ico')

        def set_icon_for_window(window_instance, current_icon_path_val):
            if not current_icon_path_val or not os.path.exists(current_icon_path_val):
                return
            try:
                window_instance.iconbitmap(default=current_icon_path_val)
            except tk.TclError as e:
                print(f"Could not set program icon ({current_icon_path_val}) for window. TclError: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while setting program icon ({current_icon_path_val}): {e}")

        settings_path = os.path.join(script_dir, 'settings.json')

        settings = {}
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                username = settings.get('username', '')
                target_texts = settings.get('restaurants', target_texts)
                notifications_enabled = settings.get('notifications_enabled', notifications_enabled)
                current_theme_name = settings.get('theme', 'dark')
                current_city_id = settings.get('city_id', "35") # Load city ID
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        active_colors = DARK_THEME if current_theme_name == 'dark' else LIGHT_THEME

        login_window = tk.Tk()
        login_window.title("Login")
        set_icon_for_window(login_window, icon_path) 
        login_window.configure(bg=LOGIN_DARK_COLOR_BG)

        window_width = 300
        window_height = 150
        screen_width = login_window.winfo_screenwidth()
        screen_height = login_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        login_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        username_frame = tk.Frame(login_window, bg=LOGIN_DARK_COLOR_BG)
        username_frame.pack(pady=15)
        username_label = tk.Label(username_frame, text="Username:", bg=LOGIN_DARK_COLOR_BG, fg=LOGIN_TEXT_COLOR_FG)
        username_label.pack(side=tk.LEFT, padx=5)
        username_entry = tk.Entry(username_frame, width=30, bg=LOGIN_TEXT_AREA_COLOR_BG, fg=LOGIN_TEXT_AREA_COLOR_FG, insertbackground=LOGIN_TEXT_AREA_COLOR_FG)
        username_entry.pack(side=tk.LEFT)
        username_entry.insert(0, username)
        username_entry.bind('<Return>', lambda e: try_login())

        password_frame = tk.Frame(login_window, bg=LOGIN_DARK_COLOR_BG)
        password_frame.pack(pady=10)
        password_label = tk.Label(password_frame, text="Password:", bg=LOGIN_DARK_COLOR_BG, fg=LOGIN_TEXT_COLOR_FG)
        password_label.pack(side=tk.LEFT, padx=5)
        password_entry = tk.Entry(password_frame, width=30, show="*", bg=LOGIN_TEXT_AREA_COLOR_BG, fg=LOGIN_TEXT_AREA_COLOR_FG, insertbackground=LOGIN_TEXT_AREA_COLOR_FG)
        password_entry.pack(side=tk.LEFT)
        password_entry.bind('<Return>', lambda e: try_login())

        login_success = False

        def try_login():
            nonlocal login_success, username, session, password
            username = username_entry.get().strip()
            password = password_entry.get()

            if not username or not password:
                messagebox.showerror("Error", "Username and password are required!", parent=login_window)
                return

            session = login_to_odi(username, password)
            if session:
                login_success = True
                settings['username'] = username
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                login_window.destroy()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.", parent=login_window)

        login_button = tk.Button(login_window, text="Login", command=try_login,
                               bg=LOGIN_BUTTON_COLOR_BG, fg=LOGIN_BUTTON_TEXT_COLOR_FG,
                               activebackground=LOGIN_BUTTON_COLOR_ACTIVE_BG,
                               activeforeground=LOGIN_BUTTON_TEXT_COLOR_FG)
        login_button.pack(pady=10)

        login_window.mainloop()

        if not login_success:
            return

        app_root = tk.Tk()
        app_root.title("odiFinder 1.3")
        set_icon_for_window(app_root, icon_path) 
        
        app_window_width = 750  # Adjusted width
        app_window_height = 450 # Kept height
        screen_width_app = app_root.winfo_screenwidth()
        screen_height_app = app_root.winfo_screenheight()
        x_app = (screen_width_app - app_window_width) // 2
        y_app = (screen_height_app - app_window_height) // 2
        app_root.geometry(f"{app_window_width}x{app_window_height}+{x_app}+{y_app}")
        
        def apply_theme_to_widgets(colors):
            app_root.configure(bg=colors["APP_BG"])
            settings_frame.configure(bg=colors["WIDGET_BG"])
            notifications_toggle.configure(bg=colors["WIDGET_BG"], fg=colors["TEXT_FG"],
                                           selectcolor=colors["SELECT_BG"],
                                           activebackground=colors["WIDGET_BG"],
                                           activeforeground=colors["TEXT_FG"])
            edit_restaurants_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                              activebackground=colors["BUTTON_ACTIVE_BG"],
                                              activeforeground=colors["BUTTON_TEXT_FG"])
            city_id_label.configure(bg=colors["WIDGET_BG"], fg=colors["TEXT_FG"])
            city_id_entry.configure(bg=colors["TEXT_AREA_BG"], fg=colors["TEXT_AREA_FG"],
                                    insertbackground=colors["ENTRY_INSERT_BG"], relief=tk.SOLID, borderwidth=1)
            save_city_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                       activebackground=colors["BUTTON_ACTIVE_BG"],
                                       activeforeground=colors["BUTTON_TEXT_FG"])
            theme_toggle_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                          activebackground=colors["BUTTON_ACTIVE_BG"],
                                          activeforeground=colors["BUTTON_TEXT_FG"])
            # getodi_button styling is specific and handled here
            getodi_button.configure(bg="#ffcf26", fg="#000000",
                                    activebackground="#ffcf26",
                                    activeforeground="#000000")
            meals_text_area.configure(bg=colors["TEXT_AREA_BG"], fg=colors["TEXT_AREA_FG"])
            controls_frame.configure(bg=colors["WIDGET_BG"])
            last_refreshed_label.configure(bg=colors["WIDGET_BG"], fg=colors["TEXT_FG"])
            interval_frame.configure(bg=colors["WIDGET_BG"])
            interval_label.configure(bg=colors["WIDGET_BG"], fg=colors["TEXT_FG"])
            interval_entry.configure(bg=colors["TEXT_AREA_BG"], fg=colors["TEXT_AREA_FG"],
                                     insertbackground=colors["ENTRY_INSERT_BG"])
            save_interval_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                           activebackground=colors["BUTTON_ACTIVE_BG"],
                                           activeforeground=colors["BUTTON_TEXT_FG"])
            button_frame.configure(bg=colors["WIDGET_BG"])
            refresh_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                     activebackground=colors["BUTTON_ACTIVE_BG"],
                                     activeforeground=colors["BUTTON_TEXT_FG"])
            # minimize_button uses theme colors
            minimize_button.configure(bg=colors["BUTTON_BG"], fg=colors["BUTTON_TEXT_FG"],
                                  activebackground=colors["BUTTON_ACTIVE_BG"],
                                  activeforeground=colors["BUTTON_TEXT_FG"])

        def toggle_theme():
            nonlocal current_theme_name, active_colors, theme_toggle_button
            if current_theme_name == "dark":
                current_theme_name = "light"
                active_colors = LIGHT_THEME
                theme_toggle_button.config(text="Dark Mode")
            else:
                current_theme_name = "dark"
                active_colors = DARK_THEME
                theme_toggle_button.config(text="Light Mode")
            
            settings['theme'] = current_theme_name
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            apply_theme_to_widgets(active_colors)

        settings_frame = tk.Frame(app_root) 
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        import webbrowser # Already imported, but good to remember it's used by open_getodi
        def open_getodi():
            webbrowser.open_new_tab("https://getodi.com")

        # Minimize button moved to settings_frame (previously getodi.com button was here)
        minimize_button = tk.Button(settings_frame, text="Minimize", command=lambda: minimize_to_tray(),
                                relief=tk.FLAT, borderwidth=0, padx=5, pady=2) 
        minimize_button.pack(side=tk.RIGHT, padx=5)


        notifications_var = tk.BooleanVar(value=notifications_enabled)
        def toggle_notifications():
            nonlocal notifications_enabled
            notifications_enabled = notifications_var.get()
            settings['notifications_enabled'] = notifications_enabled
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            print(f"Notifications {'enabled' if notifications_enabled else 'disabled'}")

        notifications_toggle = tk.Checkbutton(settings_frame, text="Send Notifications", variable=notifications_var, command=toggle_notifications,
                                     highlightthickness=0, borderwidth=0) 
        notifications_toggle.pack(side=tk.LEFT, padx=5)

        def edit_restaurants():
            nonlocal target_texts, active_colors 
            edit_window = tk.Toplevel(app_root)
            edit_window.title("Edit Restaurant List")
            edit_window.configure(bg=active_colors["APP_BG"]) 
            edit_window.transient(app_root)
            edit_window.grab_set()
            set_icon_for_window(edit_window, icon_path)

            window_width_edit = 400
            window_height_edit = 300
            parent_x = app_root.winfo_x()
            parent_y = app_root.winfo_y()
            parent_width = app_root.winfo_width()
            parent_height = app_root.winfo_height()
            x_edit = parent_x + (parent_width - window_width_edit) // 2
            y_edit = parent_y + (parent_height - window_height_edit) // 2
            edit_window.geometry(f"{window_width_edit}x{window_height_edit}+{x_edit}+{y_edit}")

            instruction_label = tk.Label(edit_window, text="Enter restaurants (one per line):",
                                         bg=active_colors["APP_BG"], fg=active_colors["TEXT_FG"]) 
            instruction_label.pack(pady=(10,5))

            text_area_font = tkFont.Font(family="Arial", size=12)
            text_area = tk.Text(edit_window, height=10, width=40,
                                font=text_area_font,
                                bg=active_colors["TEXT_AREA_BG"], fg=active_colors["TEXT_AREA_FG"], 
                                insertbackground=active_colors["ENTRY_INSERT_BG"], 
                                relief=tk.SOLID, borderwidth=1, bd=1)
            text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            text_area.insert('1.0', '\n'.join(target_texts))

            def save_restaurants_edit(): 
                new_restaurants = [r.strip() for r in text_area.get('1.0', tk.END).split('\n') if r.strip()]
                if new_restaurants:
                    target_texts[:] = new_restaurants
                    settings['restaurants'] = target_texts
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(settings, f, indent=4)
                    print("Restaurant list updated")
                    execute_meal_refresh()
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "Restaurant list cannot be empty!", parent=edit_window)

            button_frame_edit = tk.Frame(edit_window, bg=active_colors["APP_BG"]) 
            button_frame_edit.pack(pady=(5,10))

            save_button_edit = tk.Button(button_frame_edit, text="Save", command=save_restaurants_edit, 
                                    bg=active_colors["BUTTON_BG"], fg=active_colors["BUTTON_TEXT_FG"], 
                                    activebackground=active_colors["BUTTON_ACTIVE_BG"], 
                                    activeforeground=active_colors["BUTTON_TEXT_FG"], 
                                    relief=tk.FLAT, borderwidth=0, padx=10, pady=3)
            save_button_edit.pack()

        edit_restaurants_button = tk.Button(settings_frame, text="Edit Restaurants", command=edit_restaurants,
                                            relief=tk.FLAT, borderwidth=0, padx=5, pady=2) 
        edit_restaurants_button.pack(side=tk.LEFT, padx=5)

        city_id_label = tk.Label(settings_frame, text="City ID (Plate):")
        city_id_label.pack(side=tk.LEFT, padx=(10, 0))
        city_id_entry = tk.Entry(settings_frame, width=4, relief=tk.SOLID, borderwidth=1)
        city_id_entry.pack(side=tk.LEFT, padx=(2,5))
        city_id_entry.insert(0, current_city_id)

        def save_city_id_action():
            nonlocal current_city_id, settings, settings_path, app_root
            new_city_id = city_id_entry.get().strip()
            if new_city_id.isdigit() and len(new_city_id) > 0:
                current_city_id = new_city_id
                settings['city_id'] = current_city_id
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                print(f"City ID updated to {current_city_id}")
                execute_meal_refresh() 
            else:
                messagebox.showerror("Error", "City ID must be a valid number (e.g., 35).", parent=app_root)

        save_city_button = tk.Button(settings_frame, text="Set City", command=save_city_id_action,
                                     relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        save_city_button.pack(side=tk.LEFT, padx=5)

        theme_button_initial_text = "Light Mode" if current_theme_name == "dark" else "Dark Mode"
        theme_toggle_button = tk.Button(settings_frame, text=theme_button_initial_text, command=toggle_theme,
                                        relief=tk.FLAT, borderwidth=0, padx=5, pady=2) 
        theme_toggle_button.pack(side=tk.LEFT, padx=5)

        meals_font = tkFont.Font(family="Arial", size=12)
        meals_text_area = tk.Text(app_root, wrap=tk.WORD, height=15, width=60,
                                  font=meals_font,
                                  relief=tk.SOLID, borderwidth=1, bd=1) 
        meals_text_area.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)
        meals_text_area.config(state=tk.DISABLED)

        controls_frame = tk.Frame(app_root) 
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        last_refreshed_label = tk.Label(controls_frame, text="Last Refreshed: N/A") 
        last_refreshed_label.pack(side=tk.LEFT, padx=5)

        interval_frame = tk.Frame(controls_frame) 
        interval_frame.pack(side=tk.LEFT, padx=5)
        interval_label = tk.Label(interval_frame, text="Auto-refresh interval (minutes):") 
        interval_label.pack(side=tk.LEFT, padx=5)
        interval_entry = tk.Entry(interval_frame, width=5) 
        interval_entry.pack(side=tk.LEFT, padx=5)
        interval_entry.insert(0, str(settings.get('refresh_interval', 3)))

        def save_interval():
            try:
                interval = int(interval_entry.get())
                if interval <= 0:
                    messagebox.showerror("Error", "Interval must be positive.", parent=app_root)
                    return
                settings['refresh_interval'] = interval
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4)
                print(f"Auto-refresh interval updated to {interval} minutes.")
                nonlocal REFRESH_INTERVAL_MS, periodic_refresh_id 
                if periodic_refresh_id:
                    if app_root and app_root.winfo_exists():
                        app_root.after_cancel(periodic_refresh_id)
                REFRESH_INTERVAL_MS = interval * 60 * 1000
                if app_root and app_root.winfo_exists():
                    periodic_refresh_id = app_root.after(REFRESH_INTERVAL_MS, scheduled_refresh_task)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number.", parent=app_root)

        save_interval_button = tk.Button(interval_frame, text="Save", command=save_interval,
                                         relief=tk.FLAT, borderwidth=0, padx=5, pady=2) 
        save_interval_button.pack(side=tk.LEFT, padx=5)
        
        button_frame = tk.Frame(controls_frame) 
        button_frame.pack(side=tk.RIGHT)

        refresh_button = tk.Button(button_frame, text="Refresh Now", command=lambda: execute_meal_refresh(), 
                                   relief=tk.FLAT, borderwidth=0, padx=5, pady=2) 
        refresh_button.pack(side=tk.LEFT, padx=5)

        # getodi.com button moved to button_frame (previously minimize button was here)
        getodi_button = tk.Button(button_frame, text="getodi.com", command=open_getodi, 
                                  relief=tk.FLAT, borderwidth=0, padx=10, pady=2)
        getodi_button.pack(side=tk.LEFT, padx=5)


        apply_theme_to_widgets(active_colors)

        def update_gui_display(text_to_display, refresh_time_str):
            if not (app_root and app_root.winfo_exists()):
                return
            last_refreshed_label.config(text=f"Last Refreshed: {refresh_time_str}")
            meals_text_area.config(state=tk.NORMAL)
            meals_text_area.delete(1.0, tk.END)
            meals_text_area.insert(tk.END, text_to_display)
            meals_text_area.config(state=tk.DISABLED)
            app_root.update_idletasks()

        def execute_meal_refresh():
            nonlocal session, previously_found_meal_names, password, current_city_id, icon_path 
            if not (app_root and app_root.winfo_exists()):
                return

            try:
                if session is None:
                    raise requests.exceptions.RequestException("No active session")
                current_meals = check_meals(session, target_texts, current_city_id)
                refresh_time = datetime.now()
                refresh_time_str = refresh_time.strftime('%Y-%m-%d %H:%M:%S')
                output_lines = []
                current_meal_names_now = set()

                if current_meals:
                    for meal in current_meals:
                        output_lines.append(f"Restaurant: {meal['name']}")
                        output_lines.append(f"Description: {meal['description']}") 
                        output_lines.append(f"Meals available: {meal['suspended_count']}") 
                        output_lines.append("-" * 40)
                        current_meal_names_now.add(meal['name']) 
                    newly_found_meals_set = current_meal_names_now - previously_found_meal_names
                    if newly_found_meals_set and notifications_enabled and PLYER_AVAILABLE:
                        notification_title = "odiFinder: New Restaurants!"
                        new_meal_names_str = ", ".join(sorted(list(newly_found_meals_set)))
                        notification_message = f"New: {new_meal_names_str}"
                        if len(notification_message) > 250:
                            notification_message = notification_message[:247] + "..."
                        
                        notification_icon_path = None
                        if icon_path and os.path.exists(icon_path):
                            notification_icon_path = os.path.abspath(icon_path) if platform.system() == "Windows" else icon_path
                            if not os.path.exists(notification_icon_path): 
                                notification_icon_path = None

                        try:
                            if platform.system() == "Windows" and WINOTIFY_AVAILABLE:
                                toast = Notification(app_id="odiFinder", 
                                                     title=notification_title, 
                                                     msg=notification_message, 
                                                     duration="long",
                                                     icon=notification_icon_path if notification_icon_path else "") 
                                toast.set_audio(sound=audio.Default, loop=False)
                                toast.show()
                            else: 
                                notification.notify(
                                    title=notification_title, 
                                    message=notification_message,
                                    app_name="odiFinder",
                                    timeout=10,
                                    ticker="New restaurants found!",
                                    toast=True,
                                    app_icon=notification_icon_path, 
                                ) # type: ignore
                            print(f"Sent notification for new meals: {new_meal_names_str}")
                        except Exception as e:
                            print(f"Failed to send notification: {e}")
                else:
                    city_name = city_names.get(current_city_id.zfill(2), f"city {current_city_id}")
                    output_lines.append(f"No meals found for specified restaurants in {city_name} at this time.")
                previously_found_meal_names = current_meal_names_now
                update_gui_display("\n".join(output_lines), refresh_time_str)
                print(f"GUI Refreshed at {refresh_time_str}. City: {current_city_id}. Meals found: {bool(current_meals)}")

            except requests.exceptions.RequestException as e:
                error_msg = f"Connection error: {e}.\nAttempting to re-login..."
                print(error_msg)
                update_gui_display(error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                new_session = login_to_odi(username, password)
                if new_session:
                    session = new_session
                    messagebox.showinfo("Re-login Successful", "Successfully re-logged in. Meals will be refreshed shortly.", parent=app_root)
                    print("Re-login successful. Scheduling another refresh.")
                    if app_root and app_root.winfo_exists():
                         app_root.after(200, execute_meal_refresh)
                else:
                    relogin_fail_msg = "Failed to re-login. Please check credentials or network. Auto-refresh may fail."
                    messagebox.showerror("Re-login Failed", relogin_fail_msg, parent=app_root)
                    print(relogin_fail_msg)
                    update_gui_display(error_msg + "\n" + relogin_fail_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            except Exception as e:
                error_msg = f"An error occurred while updating meals: {str(e)}"
                print(error_msg)
                update_gui_display(error_msg, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        REFRESH_INTERVAL_MS = settings.get('refresh_interval', 3) * 60 * 1000

        def scheduled_refresh_task():
            nonlocal periodic_refresh_id
            if not (app_root and app_root.winfo_exists()):
                print("Scheduled refresh: Window closed or not available, stopping task.")
                return
            print("Auto-refresh for GUI triggered.")
            execute_meal_refresh()
            if app_root and app_root.winfo_exists():
                 periodic_refresh_id = app_root.after(REFRESH_INTERVAL_MS, scheduled_refresh_task)
            else:
                 periodic_refresh_id = None # Window closed during refresh

        execute_meal_refresh()
        if app_root and app_root.winfo_exists():
            periodic_refresh_id = app_root.after(REFRESH_INTERVAL_MS, scheduled_refresh_task)

        def fully_exit_app():
            nonlocal periodic_refresh_id, system_tray_icon, app_root
            print("Full application exit initiated.")
            
            # First stop the system tray icon if it exists
            if system_tray_icon:
                try:
                    if getattr(system_tray_icon, 'visible', False):
                        print("Stopping active system tray icon during full exit.")
                        system_tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping system tray icon: {e}")
                system_tray_icon = None

            # Then cancel any pending refresh tasks
            if periodic_refresh_id:
                try:
                    if app_root and app_root.winfo_exists():
                        app_root.after_cancel(periodic_refresh_id)
                        print("Cancelled periodic refresh task for full exit.")
                except tk.TclError as e:
                    print(f"Could not cancel periodic refresh (TclError) during full exit: {e}")
                except Exception as e:
                    print(f"Error cancelling periodic refresh: {e}")
                periodic_refresh_id = None
            
            # Finally destroy the window
            try:
                if app_root and app_root.winfo_exists():
                    app_root.quit()  # Stop the mainloop
                    app_root.destroy()  # Destroy the window
                    print("Application window destroyed for full exit.")
            except tk.TclError as e:
                print(f"Error destroying window: {e}")
            except Exception as e:
                print(f"Unexpected error during window destruction: {e}")

        def stop_icon_and_exit_app():
            nonlocal system_tray_icon, periodic_refresh_id, app_root
            print("Exit requested from system tray.")
            
            # First stop the system tray icon
            if system_tray_icon:
                try:
                    print("Stopping system tray icon.")
                    system_tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping system tray icon: {e}")
                system_tray_icon = None

            # Then cancel any pending refresh tasks
            if periodic_refresh_id:
                try:
                    if app_root and app_root.winfo_exists():
                        app_root.after_cancel(periodic_refresh_id)
                        print("Cancelled periodic refresh task from tray exit.")
                except tk.TclError as e:
                    print(f"Could not cancel periodic refresh (Error: {e}) during tray exit.")
                except Exception as e:
                    print(f"Error cancelling periodic refresh: {e}")
                periodic_refresh_id = None
            
            # Finally destroy the window
            try:
                if app_root and app_root.winfo_exists():
                    app_root.quit()  # Stop the mainloop
                    app_root.destroy()  # Destroy the window
                    print("Destroying application window from tray exit.")
            except tk.TclError as e:
                print(f"Error destroying window: {e}")
            except Exception as e:
                print(f"Unexpected error during window destruction: {e}")
        
        def show_window():
            nonlocal system_tray_icon, app_root
            if system_tray_icon:
                try:
                    if getattr(system_tray_icon, 'visible', False):
                        print("Stopping system tray icon to show window.")
                        system_tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping system tray icon: {e}")
                system_tray_icon = None
            
            if app_root:
                try:
                    if not app_root.winfo_exists():
                        print("Cannot show window: app_root tk widget does not exist.")
                        return
                    app_root.deiconify()
                    app_root.lift()
                    app_root.focus_force()
                    print("Application window shown.")
                except tk.TclError as e:
                    print(f"Error showing window (TclError): {e}. Window might be already destroyed.")
                except Exception as e:
                    print(f"Unexpected error showing window: {e}")
            else:
                print("Cannot show window: app_root is None.")

        def minimize_to_tray():
            nonlocal system_tray_icon, app_root, icon_path
            print("Minimizing to system tray.")
            if not (app_root and app_root.winfo_exists()):
                print("Cannot minimize: app_root not available.")
                return

            try:
                app_root.withdraw()
            except tk.TclError as e:
                print(f"Error minimizing window: {e}")
                return

            if PILLOW_AVAILABLE and PYSTRAY_AVAILABLE and icon_path and os.path.exists(icon_path):
                if system_tray_icon and getattr(system_tray_icon, 'visible', False):
                    print("System tray icon already visible. Not creating a new one.")
                    return
                try:
                    if system_tray_icon:
                        try:
                            system_tray_icon.stop()
                        except Exception as e:
                            print(f"Error stopping existing system tray icon: {e}")
                    
                    image = Image.open(icon_path)
                    menu = pystray.Menu(
                        pystray.MenuItem("Show", show_window),
                        pystray.MenuItem("Exit", stop_icon_and_exit_app)
                    )
                    system_tray_icon = pystray.Icon("odiFinder", image, "odiFinder", menu)
                    
                    import threading
                    thread = threading.Thread(target=system_tray_icon.run, daemon=True)
                    thread.start()
                    print("System tray icon started in a new thread.")
                except Exception as e:
                    print(f"Failed to create/run system tray icon: {e}")
                    try:
                        if app_root and app_root.winfo_exists():
                            app_root.deiconify()
                            messagebox.showerror("Tray Error", f"Could not minimize to system tray: {e}\nWindow will remain visible.", parent=app_root)
                    except tk.TclError:
                        pass
            else:
                missing_deps = []
                if not PILLOW_AVAILABLE: missing_deps.append("Pillow")
                if not PYSTRAY_AVAILABLE: missing_deps.append("pystray")
                if not (icon_path and os.path.exists(icon_path)): missing_deps.append("icon file")
                
                msg = "Cannot minimize to tray. Missing: " + ", ".join(missing_deps) + ".\nWindow hidden. Use Task Manager to close if needed."
                print(msg)
                try:
                    messagebox.showwarning("Minimize Info", msg, parent=app_root if app_root and app_root.winfo_exists() else None)
                except tk.TclError:
                    pass

        app_root.protocol("WM_DELETE_WINDOW", fully_exit_app)
        try:
            app_root.mainloop()
        except Exception as e:
            print(f"Error in mainloop: {e}")
        finally:
            print("Main function's finally block: Starting cleanup.")
            if system_tray_icon:
                try:
                    if getattr(system_tray_icon, 'visible', False):
                        print("Main finally: Stopping system tray icon.")
                        system_tray_icon.stop()
                except Exception as e:
                    print(f"Error stopping system tray icon in finally block: {e}")
                system_tray_icon = None

            if app_root:
                try:
                    if app_root.winfo_exists():
                        print("Ensuring app_root cleanup from finally block.")
                        if periodic_refresh_id:
                            try:
                                app_root.after_cancel(periodic_refresh_id)
                                print("Cancelled periodic refresh from finally block.")
                            except Exception as e:
                                print(f"Could not cancel periodic refresh from finally block: {e}")
                        app_root.quit()
                        app_root.destroy()
                        print("Destroyed app_root from finally block.")
                except tk.TclError as e:
                    print(f"Error in finally block cleanup: {e}")
                except Exception as e:
                    print(f"Unexpected error in finally block cleanup: {e}")
            else:
                print("app_root was None or already cleaned up prior to finally.")
            print("Main function's finally block: Cleanup attempt finished.")

    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C in console).")
    except Exception as e:
        print(f"An unexpected error occurred in the main function: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("Main function's finally block: Starting cleanup.")
        if system_tray_icon and getattr(system_tray_icon, 'visible', False):
            print("Main finally: Stopping system tray icon.")
            system_tray_icon.stop()
        system_tray_icon = None

        if app_root and app_root.winfo_exists():
            print("Ensuring app_root cleanup from finally block.")
            if periodic_refresh_id:
                try:
                    app_root.after_cancel(periodic_refresh_id)
                    print("Cancelled periodic refresh from finally block.")
                except Exception:
                    print("Could not cancel periodic refresh from finally block (error during cancel).")
            app_root.destroy()
            print("Destroyed app_root from finally block.")
        elif app_root is None:
             print("app_root was None or already cleaned up prior to finally.")
        else:
             print("app_root object exists but window was already destroyed prior to finally.")
        print("Main function's finally block: Cleanup attempt finished.")
if __name__ == "__main__":
    main()