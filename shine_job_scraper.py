from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Configure Selenium
options = Options()
options.add_argument('--headless')  # Remove this line if you want to see browser
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Auto-download ChromeDriver
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

base_url = "https://www.shine.com/job-search/jobs?job_type=2&top_companies_boost=true&sort=1&page={}"

job_titles = []
companies = []
locations = []
posted_dates = []

max_pages = 100  # Scrape 100+ pages

for page in range(1, max_pages + 1):
    print(f"Scraping page {page}...")
    driver.get(base_url.format(page))
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "jobCard_jobCard__jjUmu"))
        )
        jobs = driver.find_elements(By.CLASS_NAME, "jobCard_jobCard__jjUmu")

        for job in jobs:
            try:
                title = job.find_element(By.CLASS_NAME, "jobCard_jobTitle__jjUmu").text
                company = job.find_element(By.CLASS_NAME, "jobCard_companyName__vZMqJ").text
                location = job.find_element(By.CLASS_NAME, "jobCard_location__2EOr5").text
                posted = job.find_element(By.CLASS_NAME, "jobCard_jobPosted__cP6aA").text
            except Exception:
                continue

            job_titles.append(title)
            companies.append(company)
            locations.append(location)
            posted_dates.append(posted)

    except Exception as e:
        print(f"Failed on page {page}: {e}")
        continue

    time.sleep(1)

driver.quit()

# Save to DataFrame
df = pd.DataFrame({
    'Job Title': job_titles,
    'Company': companies,
    'Location': locations,
    'Posted': posted_dates
})

df.to_csv('shine_jobs.csv', index=False)
print(f"Scraped {len(df)} jobs.")
