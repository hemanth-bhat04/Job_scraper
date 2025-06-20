import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os
import random

# SETTINGS
CSV_FILENAME = "foundit_jobs_fresh.csv"
SAVE_EVERY_JOB = True
URL_TEMPLATE = "https://www.foundit.in/srp/results?sort=1&limit=15&query=software%2C%22Data+Scientist%22%2C%22Data+Analyst%22%2C%22Web+Developer%22%2C%22Back+end+Developer%22%2C%22IT+Consultant%22%2C%22Software+Developer%22&queryDerived=true&experienceRanges=0~1&page={}"

# INIT BROWSER
options = uc.ChromeOptions()
# ❌ DO NOT USE HEADLESS for Foundit scraping
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 12)

# TRACKERS
jobs = []
job_seen_ids = set()
job_count = 0

# SAVE TO CSV
def save_job(job):
    file_exists = os.path.exists(CSV_FILENAME)
    with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=job.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(job)

print("\n🔍 Opening: ENTRY-LEVEL TECH JOBS")

# SCRAPER LOOP
for page in range(1, 100):
    url = URL_TEMPLATE.format(page)
    print(f"\n📄 Scraping Page {page} | {url}")
    try:
        driver.get(url)
        time.sleep(random.uniform(4.5, 6.5))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobCard_jobCard__jjUmu")))
        cards = driver.find_elements(By.CSS_SELECTOR, "div.jobCard_jobCard__jjUmu")
    except Exception as e:
        print(f"❌ Failed to load page {page}: {e}")
        continue

    if not cards:
        print("⚠️ No job cards found.")
        break

    for idx, card in enumerate(cards):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(random.uniform(1.5, 2.5))

            try:
                ActionChains(driver).move_to_element(card).pause(0.4).click().perform()
                time.sleep(random.uniform(3, 5))
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", card)
                    time.sleep(random.uniform(3, 5))
                except:
                    print(f"⚠️ Could not click card {idx}. Skipping.")
                    continue

            # SKIP EXPIRED
            if "Job expired" in driver.page_source:
                print(f"⛔ Skipping expired job {idx}")
                continue

            # LEFT PANEL DATA
            try:
                title = card.find_element(By.TAG_NAME, "h3").text.strip()
            except:
                title = ""
            try:
                company = card.find_element(By.CSS_SELECTOR, "span.company-name span").text.strip()
            except:
                company = ""
            salary = location = posted = ""
            try:
                spans = card.find_elements(By.CSS_SELECTOR, "div.jobCard_jobDetails__jD83W > span")
                for span in spans:
                    txt = span.text
                    if "LPA" in txt or "₹" in txt:
                        salary = txt
                    elif any(x in txt for x in ["India", "Remote", "Bangalore", "Chennai", "Hyderabad"]):
                        location = txt
                    elif "Posted" in txt:
                        posted = txt
            except:
                pass

            # RIGHT PANEL DESCRIPTION
            try:
                desc_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#jdSection > div.jdContent")))
                description = desc_elem.text.strip()
            except:
                description = "Description not available"

            job_id = f"{title}-{company}-{location}-{posted}"
            if job_id in job_seen_ids or not title:
                continue

            job_seen_ids.add(job_id)
            job = {
                "Title": title,
                "Company": company,
                "Location": location,
                "Salary": salary,
                "Posted": posted,
                "Description": description
            }
            jobs.append(job)
            job_count += 1
            print(f"✅ {job_count}. {title} @ {company}")

            if SAVE_EVERY_JOB:
                save_job(job)
                time.sleep(random.uniform(2.2, 4.5))

        except Exception as e:
            print(f"⚠️ Error parsing card {idx}: {e}")
            continue

# CLEANUP
driver.quit()
print(f"\n🏁 FINISHED. Total jobs scraped: {job_count}")
