"""
Changelog:
2024-03-21: Fixed an error where meals with 0 suspended count were incorrectly included in results
2024-12-XX: Updated to check for "Askıdan Ücretsiz Al" button instead of counting suspended meals
2025-08-10: Updated to detect availability via "Bu menüyü askıdan al <N>" where N>0 means available
"""

import requests
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Set

def login_to_odi(username, password) -> Optional[requests.Session]:
    """
    Attempts to log in to getodi.com with the given username and password.
    Returns a requests.Session object if successful, otherwise None.
    """
    login_url = "https://getodi.com/sign-in/"
    session = requests.Session()
    login_data = {
        "username": username,
        "password": password
    }
    try:
        response = session.post(login_url, data=login_data)
        if response.status_code == 200:
            # Check if login was actually successful (e.g., not on login page anymore)
            if 'wrong_credentials' in response.url or "sign-in" in response.url:
                print("Login failed in network.py. Incorrect credentials or still on login page.")
                return None
            print("Login successful in network.py.")
            return session
        else:
            print(f"Login failed in network.py. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during login in network.py: {e}")
        return None

def check_meals(session: requests.Session, target_texts: List[str], city_id: str = "35") -> Optional[List[Dict[str, Any]]]:
    """
    Uses the session to check the meals page and search for target texts.
    New logic: A restaurant is considered available if the text matches
    "Bu menüyü askıdan al <N>" and N is greater than 0. If N is 0, it's not available.
    Returns a list of found meals or None if there is an error.
    """
    meals_url = f"https://getodi.com/student/?city={city_id}"
    try:
        response = session.get(meals_url)
        if response.ok:
            soup = BeautifulSoup(response.text, 'html.parser')
            meals_data: List[Dict[str, Any]] = []
            found_meals: Set[str] = set()

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
                        # Extract text from this menu box and search for pattern: "Bu menüyü askıdan al <N>"
                        all_text_in_menu_box_original = menu_box.get_text(" ", strip=True)
                        match = re.search(r"bu menüyü askıdan al\s*(\d+)", all_text_in_menu_box_original, flags=re.IGNORECASE)
                        if not match:
                            # If pattern not found, skip this menu box
                            continue
                        try:
                            suspended_count = int(match.group(1))
                        except ValueError:
                            suspended_count = 0

                        if suspended_count > 0:
                            actual_restaurant_name_display = menu_title_text or restaurant_name_text or target_text
                            actual_meal_name = restaurant_name_text or "No meal name available."
                            actual_location = menu_details_text or "No location available."

                            meal_info = {
                                'restaurant_name': actual_restaurant_name_display,
                                'meal_name': actual_meal_name,
                                'location': actual_location,
                                'available_count': suspended_count,
                                'available': True,
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            meals_data.append(meal_info)
                            found_meals.add(target_text)
                            break
            
            return meals_data
        else:
            print(f"Failed to access the meals page in network.py. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while checking meals in network.py: {e}")
        return None 