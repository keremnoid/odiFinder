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
    Returns a list of found meals, including suspended counts, or None if there is an error.
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
                        
                        actual_restaurant_name_display = menu_title_text or restaurant_name_text or target_text
                        actual_description = menu_details_text or "No description available."

                        meal_info = {
                            'name': actual_restaurant_name_display,
                            'description': actual_description,
                            'suspended_count': suspended_count,
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