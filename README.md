# odiFinder

A desktop application that automatically checks the available restaurants on [Odi (Öğrenci Dostu İşletme)](https://getodi.com/) and notifies the user.

## Features

- Login with your getodi.com account
- Monitors meal lists of user-selected restaurants
- Notifications when a target restaurant is found
- Customizable restaurant list
- Uses simple Tkinter GUI
- Automatic periodic refresh (default 3 minutes, user can change it in GUI)
- Minimize to system tray support
- Dark/Light theme support
- City selection support (all cities in Turkey)
- Minimize to system tray functionality

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/keremnoid/odiFinder.git
   cd odiFinder
   ```

2. **Install required Python packages:**

   - For Windows
   ```sh
   pip install requests beautifulsoup4 winotify pillow pystray
   ```
   - For other operating systems
   ```sh
   pip install requests beautifulsoup4 plyer pillow pystray
   ```

3. **Run the application:**
   ```sh
   python odiFinder.pyw
   ```

## Usage

- Enter your getodi.com username and password in the login window
- Edit the restaurant list as you wish
- Select your city using the city ID (plate number)
- Toggle between dark and light themes
- Enable/disable notifications
- The app will automatically check for your selected restaurants and notify you if they are available
- Click "Minimize" to send the app to system tray
- Right-click the system tray icon to show the window or exit the application

## Notes

- Settings are saved in `settings.json` in the same folder
- The app uses your system's default notification system
- City IDs can be found in the Turkish license plate system (e.g., 35 for İzmir)
- The app will continue running in the system tray when minimized
