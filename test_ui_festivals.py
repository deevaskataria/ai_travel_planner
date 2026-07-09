from playwright.sync_api import sync_playwright
import time

def extract_festival_text(page):
    cols = page.locator('div[data-testid="stColumn"]')
    count = cols.count()
    results = []
    for i in range(count):
        col = cols.nth(i)
        if "Match Score" in col.inner_text():
            city_name = col.locator("h3").first.inner_text()
            text = col.inner_text()
            fest_line = [line for line in text.split('\n') if "Upcoming:" in line or "No major festivals" in line]
            if fest_line:
                results.append(f"{city_name}: {fest_line[0]}")
    return results

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8501")
    page.wait_for_selector('h1', timeout=15000)
    
    print("--- Test Case 1: India destination (Udaipur) ---")
    page.locator('label', has_text='Only recommend destinations in India').check()
    page.locator('.stMultiSelect input').fill('history')
    page.keyboard.press('Enter')
    page.locator('.stMultiSelect input').fill('romantic')
    page.keyboard.press('Enter')
    time.sleep(1)
    page.locator('button', has_text='Find My Trip').click()
    time.sleep(8)
    
    print("\n".join(extract_festival_text(page)))
    
    print("\n--- Test Case 2: India destination NO CSV (Shimla/Bangalore) ---")
    # clear and search
    page.locator('.stMultiSelect input').click()
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    
    page.locator('.stMultiSelect input').fill('tech')
    page.keyboard.press('Enter')
    page.locator('button', has_text='Find My Trip').click()
    time.sleep(8)
    print("\n".join(extract_festival_text(page)))
    
    print("\n--- Test Case 3: Global destination (Paris) ---")
    page.locator('label', has_text='Only recommend destinations in India').uncheck()
    page.locator('.stMultiSelect input').click()
    page.keyboard.press('Backspace')
    
    page.locator('.stMultiSelect input').fill('romantic')
    page.keyboard.press('Enter')
    page.locator('.stMultiSelect input').fill('culture')
    page.keyboard.press('Enter')
    page.locator('button', has_text='Find My Trip').click()
    time.sleep(8)
    print("\n".join(extract_festival_text(page)))
    
    print("\n--- Test Case 4: Global destination NO DATA (Interlaken) ---")
    page.locator('.stMultiSelect input').click()
    page.keyboard.press('Backspace')
    page.keyboard.press('Backspace')
    page.locator('.stMultiSelect input').fill('skiing')
    page.keyboard.press('Enter')
    page.locator('button', has_text='Find My Trip').click()
    time.sleep(8)
    print("\n".join(extract_festival_text(page)))
    
    browser.close()
