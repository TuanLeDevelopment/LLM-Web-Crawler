from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from urllib.parse import urlparse, urljoin
import json
import os

output_file = 'mapped_site.json'
input_file = 'input_locations.json'

def load_mapped_site():
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            return set(json.load(file))
    return set()

def load_input_locations():
    if os.path.exists(input_file):
        with open(input_file, 'r') as file:
            return json.load(file)
    return {}

def save_mapped_site(mapped_site):
    with open(output_file, 'w') as file:
        json.dump(list(mapped_site), file, indent=4)

def save_input_locations(input_locations):
    with open(input_file, 'w') as file:
        json.dump(input_locations, file, indent=4)

def visit_page(url):
    try:
        driver.get(url)
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed to load {url}: {e}")

def get_links():
    retry_count = 3
    for attempt in range(retry_count):
        try:
            elements = driver.find_elements(By.TAG_NAME, 'a')
            links = [elem.get_attribute('href') for elem in elements if elem.get_attribute('href')]
            return links
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    return []

def find_inputs():
    input_elements = driver.find_elements(By.TAG_NAME, 'input')
    button_elements = driver.find_elements(By.TAG_NAME, 'button')
    inputs = [elem.get_attribute('outerHTML') for elem in input_elements]
    buttons = [elem.get_attribute('outerHTML') for elem in button_elements]
    return inputs, buttons

def contains_login_keywords(page_source):
    login_keywords = ["login", "sign in", "signing in", "authentication", "log in", "username/password"]
    return any(keyword in page_source for keyword in login_keywords)

def simulate_interactions_and_check_login():
    elements_to_check = driver.find_elements(By.XPATH, "//button | //input[@type='submit'] | //a")

    for element in elements_to_check:
        try:
            original_page_source = driver.page_source
            element.click()
            time.sleep(1)  # Wait for potential redirect or change
            current_page_source = driver.page_source.lower()

            if original_page_source != current_page_source:
                if contains_login_keywords(current_page_source):
                    return True
                else:
                    driver.back()
                    time.sleep(0.5)  # Wait for the page to go back
        except Exception as e:
            print(f"Interaction failed: {e}")
            continue

    return False

def is_valid_url(url, base_url):
    parsed_url = urlparse(url)
    base_parsed_url = urlparse(base_url)
    return parsed_url.scheme in ['http', 'https'] and parsed_url.netloc == base_parsed_url.netloc

def map_site(start_url, base_url, max_depth=1, current_depth=0):
    global mapped_site, input_locations

    if current_depth > max_depth:
        return mapped_site

    if not is_valid_url(start_url, base_url):
        print(f"Invalid URL or outside domain: {start_url}")
        return mapped_site

    visit_page(start_url)
    mapped_site.add(start_url)

    save_mapped_site(mapped_site)

    inputs, buttons = find_inputs()
    login_required = simulate_interactions_and_check_login()
    
    input_locations[start_url] = {
        'inputs': inputs,
        'buttons': buttons,
        'login_required': login_required
    }

    save_input_locations(input_locations)

    links = get_links()
    for link in links:
        absolute_link = urljoin(base_url, link)
        if absolute_link not in mapped_site and is_valid_url(absolute_link, base_url):
            map_site(absolute_link, base_url, max_depth, current_depth + 1)

    return mapped_site

options = webdriver.ChromeOptions()
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

driver = webdriver.Chrome(options=options)

start_url = 'http://localhost:8080/'

# Reset the mapped_site and input_locations
mapped_site = set()
input_locations = {}

# Save the initial state
save_mapped_site(mapped_site)
save_input_locations(input_locations)

mapped_site = map_site(start_url, start_url)
print(mapped_site)

print(f"Site map saved to {output_file}")
print(f"Input locations saved to {input_file}")

# Keep the browser open
input("Press Enter to close the browser...")

driver.quit()
