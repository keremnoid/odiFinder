"""
Changelog:
2024-03-21: Fixed an error where meals with 0 suspended count were incorrectly included in results
2024-12-XX: Updated to check for "Askıdan Ücretsiz Al" button instead of counting suspended meals
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
    Returns a list of found meals with available "Askıdan Ücretsiz Al" button, or None if there is an error.
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
                        # First check if there's a message indicating no meals left
                        all_text_in_menu_box = menu_box.get_text(strip=True).lower()
                        if 'askıda yemek kalmadı' in all_text_in_menu_box or 'askıda yemek yok' in all_text_in_menu_box:
                            # Skip this restaurant - no meals available
                            continue
                            
                        # Check if "Askıdan Ücretsiz Al" button is available and active
                        free_button_available = False
                        
                        # Look for elements containing "askıdan" and "ücretsiz" text
                        button_containers = menu_box.find_all(['button', 'a', 'div'])
                        for container in button_containers:
                            if isinstance(container, Tag):
                                container_text = container.get_text(strip=True).lower()
                                if 'askıdan' in container_text and 'ücretsiz' in container_text:
                                    # Check if button is not disabled
                                    disabled_attr = container.get('disabled')
                                    class_attr = container.get('class')
                                    onclick_attr = container.get('onclick')
                                    
                                    # Check for disabled class
                                    if class_attr is None:
                                        disabled_in_class = False
                                    elif isinstance(class_attr, list):
                                        disabled_in_class = 'disabled' in class_attr
                                    else:
                                        disabled_in_class = 'disabled' in str(class_attr)
                                    
                                    # Check for onclick="return false;" which indicates no meals available
                                    onclick_disabled = onclick_attr and 'return false' in str(onclick_attr)
                                    
                                    if not disabled_attr and not disabled_in_class and not onclick_disabled:
                                        # Additional check - button should not have text indicating unavailability
                                        if 'yok' not in container_text and 'bitti' not in container_text:
                                            free_button_available = True
                                            break
                        
                        if free_button_available:
                            actual_restaurant_name_display = menu_title_text or restaurant_name_text or target_text
                            actual_meal_name = restaurant_name_text or "No meal name available."
                            actual_location = menu_details_text or "No location available."

                            meal_info = {
                                'restaurant_name': actual_restaurant_name_display,
                                'meal_name': actual_meal_name,
                                'location': actual_location,
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