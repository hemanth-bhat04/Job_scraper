import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def get_job_cards(driver):
    return driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.rounded-lg.bg-white.relative.w-auto.cursor-pointer")

def scroll_into_view(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.5)

def click_card(driver, card):
    try:
        scroll_into_view(driver, card)
        ActionChains(driver).move_to_element(card).pause(0.3).click().perform()
        return True
    except Exception as e:
        print("⚠️ Click failed, trying JS click fallback...")
        try:
            driver.execute_script("arguments[0].click();", card)
            return True
        except Exception as e2:
            print("❌ JS click failed:", e2)
            return False

def extract_job_description(driver):
    try:
        desc_box = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "jobDescription"))
        )
        return desc_box.text
    except Exception:
        return "Description not available."

def extract_basic_info(card):
    try:
        title = card.find_element(By.CSS_SELECTOR, "div.text-content-primary.font-bold").text
    except: title = ""
    try:
        company = card.find_element(By.CSS_SELECTOR, "div.text-content-secondary").text
    except: company = ""
    try:
        location = card.find_element(By.CSS_SELECTOR, "a[href*='/search/jobs-in']").text
    except: location = ""
    try:
        posted = card.find_element(By.CSS_SELECTOR, "div.text-content-tertiary span").text
    except: posted = ""
    return {"title": title, "company": company, "location": location, "posted": posted}

def scrape_jobs(keyword="web", max_pages=2):
    driver = init_driver()
    results = []
    base_url = "https://www.foundit.in/search/entry-level-jobs?query={}&experienceRanges=0~1&start={}"

    for page in range(max_pages):
        print(f"\n📄 Scraping Page {page+1}")
        driver.get(base_url.format(keyword, page * 20))
        time.sleep(2)

        job_cards = get_job_cards(driver)
        if not job_cards:
            print("❌ No job cards found")
            continue

        for i, card in enumerate(job_cards):
            print(f"➡️ Card {i}")
            try:
                if not click_card(driver, card):
                    raise Exception("Click failed")

                time.sleep(1)  # wait for right panel
                info = extract_basic_info(card)
                info["description"] = extract_job_description(driver)
                results.append(info)
            except Exception as e:
                print(f"⚠️ Error parsing card {i} on page {page+1}: {e}")
                continue

    driver.quit()
    return results

if __name__ == "__main__":
    data = scrape_jobs(keyword="tech", max_pages=10)
    df = pd.DataFrame(data)
    df.to_csv("foundit_entry_tech_jobs.csv", index=False)
    print("✅ DONE. Jobs scraped:", len(df))
