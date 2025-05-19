# odiFinder

A desktop application that automatically checks the available restaurants on [Odi (Öğrenci Dostu İşletme)](getodi.com) and notifies the user.

## Features

- Login with your getodi.com account
- Monitors meal lists of user-selected restaurants
- Sound notifications when a target restaurant is found
- Customizable restaurant list
- Uses simple Tkinter GUI
- Automatic periodic refresh (5 minutes, can be changed in the code)

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/keremnoid/odiFinder.git
   cd odiFinder
   ```

2. **Install required Python packages:**
   ```sh
   pip install requests beautifulsoup4
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
- Sound notifications require Windows (`winsound` module).
- Settings are saved in `settings.json` in the same folder.
