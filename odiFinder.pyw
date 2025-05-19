import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import json
import tkinter as tk
from tkinter import messagebox
# winsound only works on Windows.
try:
    import winsound
    sound_available = True
except ImportError:
    sound_available = False
    print("Warning: winsound module not found. Sound notifications not available.")
from tkinter import simpledialog
import os
import tkinter.font as tkFont
import locale

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
             # Girişin başarılı olup olmadığını yanıtın içeriğini kontrol ederek teyit edin
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

def check_meals(session, target_texts):
    """
    Uses the session to check the meals page and search for target texts.
    Returns a list of found meals, or None if there is an error.
    """
    # You may need to verify the meals URL by inspecting the website. (for future updates or other cities. right now only izmir is supported, easily changeable by changing the city id)
    meals_url = "https://getodi.com/student/?city=35"
    try:
        response = session.get(meals_url)
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            meals_data = []
            found_meals = set()  # To track found meals
            # Find all text elements and check for target texts
            # You can target specific HTML elements for a more efficient search.
            for element in soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a']):
                element_text = element.get_text().strip()
                for target_text in target_texts:
                    # Case-insensitive search
                    if target_text.lower() in element_text.lower() and target_text not in found_meals:
                        meal_info = {
                            'name': target_text,
                            'details': 'Found.', # Detaylar web sitesinden çekilebilir
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        meals_data.append(meal_info)
                        found_meals.add(target_text)  # Mark this meal as found
                        # Break the inner loop once a target text is found, to avoid adding the same text again
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
    # Dark Theme Colors
    DARK_COLOR_BG = "#2E2E2E"          # Main background for windows
    WIDGET_COLOR_BG = "#3C3C3C"        # Background for frames, labels, checkbuttons
    BUTTON_COLOR_BG = "#505050"        # Button background
    BUTTON_COLOR_ACTIVE_BG = "#6A6A6A" # Button active/hover background
    TEXT_COLOR_FG = "#E0E0E0"          # General text foreground (light gray)
    TEXT_AREA_COLOR_BG = "#1E1E1E"     # Text area background (very dark)
    TEXT_AREA_COLOR_FG = "#D0D0D0"     # Text area foreground
    SELECT_COLOR_BG = "#4A4A4A"        # Background for selected checkbutton indicator
    BUTTON_TEXT_COLOR_FG = "#FFFFFF"   # Pure white for button text for better contrast

    app_root = None  # Main application window, initialized to None
    periodic_refresh_id = None # ID for the scheduled Tkinter .after job
    previously_found_meal_names = set() # To track meals for notification logic

    PLYER_AVAILABLE = False
    try:
        from plyer import notification as plyer_notification
        PLYER_AVAILABLE = True
    except ImportError:
        print("Plyer library not found. Windows notifications will be disabled. "
              "Install it with 'pip install plyer'.")

    # Variables to be loaded or set, ensure they have default values or are checked
    username = ''
    password = ''
    target_texts = ["Cafe Rien", "Nazilli Pide Kebap Çorba Salonu", "Çıtır Pide"]
    notifications_enabled = True # Changed from sound_enabled
    session = None

    try:
        # Get current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(script_dir, 'settings.json')

        # Load saved settings
        settings = {}
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                username = settings.get('username', '')
                target_texts = settings.get('restaurants', target_texts)
                notifications_enabled = settings.get('notifications_enabled', notifications_enabled) # Changed key
        except (FileNotFoundError, json.JSONDecodeError):
            # If settings file doesn't exist or is corrupted, use defaults
            pass

        # Create login dialog
        login_window = tk.Tk()
        login_window.title("Login")
        login_window.configure(bg=DARK_COLOR_BG)

        # Center the window
        window_width = 300
        window_height = 150
        screen_width = login_window.winfo_screenwidth()
        screen_height = login_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        login_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Username frame
        username_frame = tk.Frame(login_window, bg=DARK_COLOR_BG)
        username_frame.pack(pady=15)
        username_label = tk.Label(username_frame, text="Username:", bg=DARK_COLOR_BG, fg=TEXT_COLOR_FG)
        username_label.pack(side=tk.LEFT, padx=5)
        username_entry = tk.Entry(username_frame, width=30, bg=TEXT_AREA_COLOR_BG, fg=TEXT_AREA_COLOR_FG, insertbackground=TEXT_AREA_COLOR_FG)
        username_entry.pack(side=tk.LEFT)
        username_entry.insert(0, username)  # Pre-fill username if available
        username_entry.bind('<Return>', lambda e: try_login())

        # Password frame
        password_frame = tk.Frame(login_window, bg=DARK_COLOR_BG)
        password_frame.pack(pady=10)
        password_label = tk.Label(password_frame, text="Password:", bg=DARK_COLOR_BG, fg=TEXT_COLOR_FG)
        password_label.pack(side=tk.LEFT, padx=5)
        password_entry = tk.Entry(password_frame, width=30, show="*", bg=TEXT_AREA_COLOR_BG, fg=TEXT_AREA_COLOR_FG, insertbackground=TEXT_AREA_COLOR_FG)
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

        # Login button
        login_button = tk.Button(login_window, text="Login", command=try_login,
                               bg=BUTTON_COLOR_BG, fg=BUTTON_TEXT_COLOR_FG,
                               activebackground=BUTTON_COLOR_ACTIVE_BG,
                               activeforeground=BUTTON_TEXT_COLOR_FG)
        login_button.pack(pady=10)

        login_window.mainloop()

        if not login_success:
            return  # Exit if login failed or window was closed

        # Create the main application window
        app_root = tk.Tk()
        app_root.title("odiFinder 1.1") # Version updated
        app_root.geometry("550x450") # Set a reasonable default size
        app_root.configure(bg=DARK_COLOR_BG)

        # --- GUI Elements ---
        controls_frame = tk.Frame(app_root, bg=WIDGET_COLOR_BG)
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        last_refreshed_label = tk.Label(controls_frame, text="Last Refreshed: N/A",
                                        bg=WIDGET_COLOR_BG, fg=TEXT_COLOR_FG)
        last_refreshed_label.pack(side=tk.LEFT, padx=5)

        # Settings frame for notification toggle and restaurant list
        settings_frame = tk.Frame(app_root, bg=WIDGET_COLOR_BG)
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Notification toggle
        notifications_var = tk.BooleanVar(value=notifications_enabled)
        def toggle_notifications(): # Renamed from toggle_sound
            nonlocal notifications_enabled
            notifications_enabled = notifications_var.get()
            settings['notifications_enabled'] = notifications_enabled # Changed key
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            print(f"Notifications {'enabled' if notifications_enabled else 'disabled'}")

        notifications_toggle = tk.Checkbutton(settings_frame, text="Send Notifications", variable=notifications_var, command=toggle_notifications, # Text changed
                                     bg=WIDGET_COLOR_BG, fg=TEXT_COLOR_FG,
                                     selectcolor=SELECT_COLOR_BG,
                                     activebackground=WIDGET_COLOR_BG, activeforeground=TEXT_COLOR_FG,
                                     highlightthickness=0, borderwidth=0)
        notifications_toggle.pack(side=tk.LEFT, padx=5)

        # Restaurant list editor
        def edit_restaurants():
            nonlocal target_texts
            edit_window = tk.Toplevel(app_root)
            edit_window.title("Edit Restaurant List")
            edit_window.geometry("400x300")
            edit_window.configure(bg=DARK_COLOR_BG)
            edit_window.transient(app_root) # Associate with main window
            edit_window.grab_set() # Make modal

            # Center the edit window relative to the main window
            window_width_edit = 400 # Renamed to avoid conflict
            window_height_edit = 300 # Renamed to avoid conflict
            parent_x = app_root.winfo_x()
            parent_y = app_root.winfo_y()
            parent_width = app_root.winfo_width()
            parent_height = app_root.winfo_height()

            x_edit = parent_x + (parent_width - window_width_edit) // 2 # Renamed
            y_edit = parent_y + (parent_height - window_height_edit) // 2 # Renamed
            edit_window.geometry(f"{window_width_edit}x{window_height_edit}+{x_edit}+{y_edit}")


            instruction_label = tk.Label(edit_window, text="Enter restaurants (one per line):",
                                         bg=DARK_COLOR_BG, fg=TEXT_COLOR_FG)
            instruction_label.pack(pady=(10,5))

            text_area_font = tkFont.Font(family="Arial", size=12)
            text_area = tk.Text(edit_window, height=10, width=40,
                                font=text_area_font,
                                bg=TEXT_AREA_COLOR_BG, fg=TEXT_AREA_COLOR_FG,
                                insertbackground=TEXT_AREA_COLOR_FG,
                                relief=tk.SOLID, borderwidth=1, bd=1)
            text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            text_area.insert('1.0', '\n'.join(target_texts))

            def save_restaurants():
                new_restaurants = [r.strip() for r in text_area.get('1.0', tk.END).split('\n') if r.strip()]
                if new_restaurants:
                    target_texts[:] = new_restaurants
                    settings['restaurants'] = target_texts
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(settings, f, indent=4)
                    print("Restaurant list updated")
                    execute_meal_refresh()  # Refresh with new restaurant list
                    edit_window.destroy()
                else:
                    messagebox.showerror("Error", "Restaurant list cannot be empty!", parent=edit_window)

            button_frame_edit = tk.Frame(edit_window, bg=DARK_COLOR_BG)
            button_frame_edit.pack(pady=(5,10))

            save_button = tk.Button(button_frame_edit, text="Save", command=save_restaurants,
                                    bg=BUTTON_COLOR_BG, fg=BUTTON_TEXT_COLOR_FG,
                                    activebackground=BUTTON_COLOR_ACTIVE_BG, activeforeground=BUTTON_TEXT_COLOR_FG,
                                    relief=tk.FLAT, borderwidth=0, padx=10, pady=3)
            save_button.pack()

        edit_restaurants_button = tk.Button(settings_frame, text="Edit Restaurants", command=edit_restaurants,
                                            bg=BUTTON_COLOR_BG, fg=BUTTON_TEXT_COLOR_FG,
                                            activebackground=BUTTON_COLOR_ACTIVE_BG, activeforeground=BUTTON_TEXT_COLOR_FG,
                                            relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        edit_restaurants_button.pack(side=tk.LEFT, padx=5)

        meals_font = tkFont.Font(family="Arial", size=12)
        meals_text_area = tk.Text(app_root, wrap=tk.WORD, height=15, width=60,
                                  font=meals_font,
                                  bg=TEXT_AREA_COLOR_BG, fg=TEXT_AREA_COLOR_FG,
                                  relief=tk.SOLID, borderwidth=1, bd=1)
        meals_text_area.pack(padx=10, pady=(0,10), fill=tk.BOTH, expand=True)
        meals_text_area.config(state=tk.DISABLED)

        def update_gui_display(text_to_display, refresh_time_str):
            if not (app_root and app_root.winfo_exists()):
                return

            last_refreshed_label.config(text=f"Last Refreshed: {refresh_time_str}")
            meals_text_area.config(state=tk.NORMAL)
            meals_text_area.delete(1.0, tk.END)
            meals_text_area.insert(tk.END, text_to_display)
            meals_text_area.config(state=tk.DISABLED)
            app_root.update_idletasks()

        # --- Refresh Logic ---
        def execute_meal_refresh():
            nonlocal session, previously_found_meal_names, password
            if not (app_root and app_root.winfo_exists()):
                return

            try:
                current_meals = check_meals(session, target_texts)
                refresh_time = datetime.now()
                refresh_time_str = refresh_time.strftime('%Y-%m-%d %H:%M:%S')

                output_lines = []
                current_meal_names_now = set()

                if current_meals:
                    for meal in current_meals:
                        output_lines.append(f"Restaurant: {meal['name']}")
                        output_lines.append(f"Details: {meal['details']}")
                        output_lines.append("-" * 40)
                        current_meal_names_now.add(meal['name'])

                    newly_found_meals_set = current_meal_names_now - previously_found_meal_names

                    if newly_found_meals_set and notifications_enabled and PLYER_AVAILABLE:
                        notification_title = "odiFinder: New Restaurants!"
                        # Sort for consistent message order
                        new_meal_names_str = ", ".join(sorted(list(newly_found_meals_set)))
                        notification_message = f"New: {new_meal_names_str}"
                        if len(notification_message) > 250: # Basic truncation for very long lists
                            notification_message = notification_message[:247] + "..."
                        try:
                            plyer_notification.notify(
                                title=notification_title,
                                message=notification_message,
                                app_name="odiFinder",
                                timeout=10  # Notification display duration in seconds
                            )
                            print(f"Sent notification for new meals: {new_meal_names_str}")
                        except Exception as e:
                            print(f"Failed to send notification: {e}")
                else:
                    output_lines.append("No meals found for specified restaurants at this time.")

                previously_found_meal_names = current_meal_names_now # Update for next comparison

                update_gui_display("\n".join(output_lines), refresh_time_str)
                print(f"GUI Refreshed at {refresh_time_str}. Meals found: {bool(current_meals)}")

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

        # Create a frame for buttons
        button_frame = tk.Frame(controls_frame, bg=WIDGET_COLOR_BG)
        button_frame.pack(side=tk.RIGHT)

        refresh_button = tk.Button(button_frame, text="Refresh Now", command=execute_meal_refresh,
                                   bg=BUTTON_COLOR_BG, fg=BUTTON_TEXT_COLOR_FG,
                                   activebackground=BUTTON_COLOR_ACTIVE_BG, activeforeground=BUTTON_TEXT_COLOR_FG,
                                   relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        refresh_button.pack(side=tk.LEFT, padx=5)

        exit_button = tk.Button(button_frame, text="Exit", command=lambda: on_app_closing(),
                                bg=BUTTON_COLOR_BG, fg=BUTTON_TEXT_COLOR_FG,
                                activebackground=BUTTON_COLOR_ACTIVE_BG, activeforeground=BUTTON_TEXT_COLOR_FG,
                                relief=tk.FLAT, borderwidth=0, padx=5, pady=2)
        exit_button.pack(side=tk.LEFT, padx=5)

        # --- Periodic Refresh Task ---
        REFRESH_INTERVAL_MS = 3 * 60 * 1000  # 3 minutes (changed from 5 for testing, can be reverted)

        def scheduled_refresh_task():
            nonlocal periodic_refresh_id
            if not (app_root and app_root.winfo_exists()):
                print("Scheduled refresh: Window closed, stopping task.")
                return

            print("Auto-refresh for GUI triggered.")
            execute_meal_refresh()
            if app_root and app_root.winfo_exists():
                 periodic_refresh_id = app_root.after(REFRESH_INTERVAL_MS, scheduled_refresh_task)
            else:
                 periodic_refresh_id = None

        execute_meal_refresh()

        if app_root and app_root.winfo_exists():
            periodic_refresh_id = app_root.after(REFRESH_INTERVAL_MS, scheduled_refresh_task)

        def on_app_closing():
            nonlocal periodic_refresh_id
            print("Application window closing action initiated.")
            if periodic_refresh_id:
                if app_root and app_root.winfo_exists():
                    try:
                        app_root.after_cancel(periodic_refresh_id)
                        print("Cancelled periodic refresh task.")
                    except tk.TclError:
                        print("Could not cancel periodic refresh (TclError).")
                periodic_refresh_id = None
            if app_root and app_root.winfo_exists():
                app_root.destroy()
                print("Application window destroyed by on_app_closing.")

        app_root.protocol("WM_DELETE_WINDOW", on_app_closing)
        app_root.mainloop()

    except KeyboardInterrupt:
        print("\nProgram terminated by user (Ctrl+C in console).")
    except Exception as e:
        print(f"An unexpected error occurred in the main function: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("Main function's finally block: Starting cleanup.")

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
             print("app_root was not active or already cleaned up prior to finally.")
        else:
             print("app_root object exists but window was already destroyed.")

        print("Main function's finally block: Cleanup attempt finished.")
if __name__ == "__main__":
    main()
