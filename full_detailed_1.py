import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os

SAVE_INTERVAL = 1
CSV_FILENAME = "foundit_full_combined_jobs.csv"
URL = "https://www.foundit.in/srp/results?sort=1&limit=15&query=software%2C%22Data+Scientist%22%2C%22Data+Analyst%22%2C%22Web+Developer%22%2C%22Back+end+Developer%22%2C%22IT+Consultant%22%2C%22Software+Developer%22&queryDerived=true&experienceRanges=0%7E1"

driver = uc.Chrome(options=uc.ChromeOptions())
driver.set_window_size(1300, 900)
wait = WebDriverWait(driver, 10)
job_seen_ids = set()
job_count = 0

def save_job(job):
    file_exists = os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=job.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(job)

print(f"\n🔍 Opening: ENTRY-LEVEL TECH JOBS")
driver.get(URL)
time.sleep(5)

for page in range(100):
    print(f"📄 Scraping Page {page+1}")

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobCard_jobCard__jjUmu")))
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jobCard_jobCard__jjUmu")
    except:
        print("⚠️ No job cards found. Skipping page.")
        break

    if not cards:
        break

    for index, card in enumerate(cards):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(1.2)

            try:
                ActionChains(driver).move_to_element(card).pause(0.5).click().perform()
                time.sleep(3.5)
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", card)
                    time.sleep(3.5)
                except:
                    print(f"⚠️ Card {index} not clickable. Skipping.")
                    continue

            try:
                expired_check = driver.find_element(By.XPATH, "//*[contains(text(), 'Job expired')]")
                print(f"⚠️ Card {index} shows 'Job expired'. Skipping.")
                continue
            except:
                pass

            try: title = card.find_element(By.TAG_NAME, "h3").text.strip()
            except: title = ""
            try: company = card.find_element(By.CSS_SELECTOR, "span.company-name span").text.strip()
            except: company = ""

            salary = location = posted = tag = ""
            try:
                info_items = card.find_elements(By.CSS_SELECTOR, "div.jobCard_jobDetails__jD83W > span")
                for item in info_items:
                    txt = item.text
                    if ("LPA" in txt or "₹" in txt) and not salary:
                        salary = txt
                    elif any(loc in txt for loc in ["India", "Remote", "Hyderabad", "Bangalore", "Chennai"]):
                        location = txt
                    elif "Posted" in txt:
                        posted = txt
            except:
                pass

            try:
                desc_box = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.ID, "jobDescription"))
                )
                description = desc_box.text.strip()
            except:
                description = "Description not available."

            job_id = f"{title}-{company}-{location}-{posted}"
            if job_id in job_seen_ids or not title:
                continue

            job_seen_ids.add(job_id)
            job = {
                "Title": title,
                "Company": company,
                "Location": location,
                "Salary": salary,
                "Tag": tag,
                "Posted": posted,
                "Description": description
            }

            job_count += 1
            print(f"✅ {job_count}. {title} | {company} | {location}")
            save_job(job)
            time.sleep(2.5)

        except Exception as e:
            print(f"⚠️ Error parsing card {index} on page {page + 1}: {e}")
            continue

    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
        if not next_btn.is_enabled():
            break
        next_btn.click()
        time.sleep(4)
    except:
        print("🔚 No more pages.")
        break

try:
    driver.quit()
except:
    pass

print(f"\n🏁 Finished. Total jobs scraped: {job_count}")
