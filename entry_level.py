import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import csv
from selenium.common.exceptions import WebDriverException

driver = uc.Chrome(options=uc.ChromeOptions(), version_main=136)
driver.set_window_size(1300, 900)

jobs = []
job_seen_ids = set()

# Base URL for Entry-Level + Tech/Software jobs
base_url = "https://www.foundit.in/search/entry-level-jobs?query=developer&experienceRanges=0~1&functionalArea=IT%2C+Software"

page = 0
while True:
    try:
        start = page * 20
        url = f"{base_url}&start={start}"
        print(f"📄 Page {page + 1} | URL: {url}")
        driver.get(url)
        time.sleep(5)

        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.rounded-lg.bg-white.relative.w-auto.cursor-pointer")

        if not job_cards:
            print("✅ No more jobs found. Ending.")
            break

        for card in job_cards:
            try:
                # Safe extraction
                title = ""
                company = ""
                salary = ""
                location = ""
                posted = ""
                tag = ""

                # Title
                try:
                    title = card.find_element(By.TAG_NAME, "h3").text.strip()
                except: pass

                # Company
                try:
                    company = card.find_element(By.XPATH, ".//span/p").text.strip()
                except: pass

                # Rest from text lines
                lines = card.text.split("\n")
                for line in lines:
                    line = line.strip()
                    if ("LPA" in line or "₹" in line) and not salary:
                        salary = line
                    elif any(city in line for city in ["India", "Remote", "Bangalore", "Hyderabad", "Chennai", "Pune", "Delhi", "Noida"]) and not location:
                        location = line
                    elif "Posted" in line and not posted:
                        posted = line
                    elif "Apply" in line and not tag:
                        tag = line

                job_id = f"{title}-{company}-{location}-{posted}"
                if job_id not in job_seen_ids and title:
                    job_seen_ids.add(job_id)
                    jobs.append({
                        "Title": title,
                        "Company": company,
                        "Location": location,
                        "Salary": salary,
                        "Tag": tag,
                        "Posted": posted
                    })

            except Exception as e:
                print(f"⚠️ Skipped job: {e}")
                continue

        page += 1
        if page > 1000:  # Up to 20,000 jobs (1000 * 20)
            print("🚨 Max page limit hit. Stopping.")
            break

    except WebDriverException as e:
        print(f"❌ Browser crashed. Restarting...: {e}")
        driver.quit()
        time.sleep(5)
        driver = uc.Chrome(options=uc.ChromeOptions(), version_main=136)
        driver.set_window_size(1300, 900)
        continue

driver.quit()

if jobs:
    with open("entry_level_tech_jobs_foundit.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
        writer.writeheader()
        writer.writerows(jobs)
    print(f"\n✅ DONE: Saved {len(jobs)} jobs to entry_level_tech_jobs_foundit.csv")
else:
    print("❌ No jobs scraped.")
