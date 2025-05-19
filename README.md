# odiFinder

A desktop application that automatically checks the available restaurants on [Odi (Öğrenci Dostu İşletme)](https://getodi.com/) and notifies the user.

## Features

- Login with your getodi.com account
- Monitors meal lists of user-selected restaurants
- Notifications when a target restaurant is found
- Customizable restaurant list
- Uses simple Tkinter GUI
- Automatic periodic refresh (5 minutes, user can change it in GUI)

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/keremnoid/odiFinder.git
   cd odiFinder
   ```

2. **Install required Python packages:**
   ```sh
   pip install requests beautifulsoup4 plyer
   ```

3. **Run the application:**
   ```sh
   python odiFinder.pyw
   ```

## Usage

- Enter your getodi.com username and password in the login window.
- Edit the restaurant list as you wish.
- The app will automatically check for your selected restaurants and notify you if they are available.

## Notes

- Works only for İzmir city by default (can be changed in the code by changing the restaurant list link).
- Settings are saved in `settings.json` in the same folder.
