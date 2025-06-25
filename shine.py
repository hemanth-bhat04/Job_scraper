import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime

# Configure headers to mimic a browser visit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.shine.com/'
}

def scrape_job_card(card):
    """Extract job details from a single job card"""
    job = {}
    
    # Job Title
    title_elem = card.find('p', class_='jobCardNova_bigCardTopTitleHeading__Rj2sC')
    job['Title'] = title_elem.get_text(strip=True) if title_elem else None
    
    # Company Name
    company_elem = card.find('span', class_='jobCardNova_bigCardTopTitleName__M_W_m')
    job['Company'] = company_elem.get_text(strip=True) if company_elem else None
    
    # Location
    loc_elem = card.find('div', class_='jobCardNova_bigCardLocation__OMkI1')
    if loc_elem:
        loc_text = loc_elem.find('div', class_='jobCardNova_bigCardCenterListLoc__usiPB')
        job['Location'] = loc_text.get_text(strip=True) if loc_text else None
    else:
        job['Location'] = None
    
    # Experience
    exp_elem = card.find('div', class_='jobCardNova_bigCardExperience__54Ken')
    if exp_elem:
        exp_text = exp_elem.find('span', class_='jobCardNova_bigCardCenterListExp__KTSEc')
        job['Experience'] = exp_text.get_text(strip=True) if exp_text else None
    else:
        job['Experience'] = None
    
    # Posted Date
    posted_elem = card.find('span', class_='jobCardNova_postedData__LTERc')
    job['Posted'] = posted_elem.get_text(strip=True) if posted_elem else None
    
    # Skills
    skills = []
    skills_elems = card.find_all('li', class_='jobCardNova_toolTip__MPK0n')
    if skills_elems:
        skills.extend([skill.get_text(strip=True) for skill in skills_elems])
    
    # Additional skills from tooltip
    tooltip_elem = card.find('div', class_='tooltipNova_tooltip__WGL5G')
    if tooltip_elem:
        additional_skills = tooltip_elem.get_text(strip=True).split(',')
        skills.extend([skill.strip() for skill in additional_skills])
    job['Skills'] = ', '.join(skills) if skills else None
    
    # Job URL
    url_elem = card.find('meta', itemprop='url')
    job['URL'] = url_elem['content'] if url_elem else None
    
    # Hiring Status
    hiring_elem = card.find('div', class_='jobTypeTagNova_hiringTag__xiY4f')
    job['Hiring_Status'] = hiring_elem.get_text(strip=True) if hiring_elem else None
    
    # Salary (if available)
    salary_elem = card.find('div', class_='jobCardNova_bigCardSalary__XH5q_')
    job['Salary'] = salary_elem.get_text(strip=True) if salary_elem else None
    
    # Timestamp
    job['Scraped_At'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return job

def scrape_page(url, page_num):
    """Scrape a single page of job listings"""
    try:
        # Add pagination parameter
        paginated_url = f"{url}&page={page_num}"
        print(f"Scraping page {page_num}: {paginated_url}")
        
        response = requests.get(paginated_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch page {page_num}. Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('div', class_='jobCardNova_bigCard__W2xn3')
        
        if not job_cards:
            print(f"No job cards found on page {page_num}")
            return None
        
        jobs = []
        for card in job_cards:
            job = scrape_job_card(card)
            if job:
                jobs.append(job)
        
        return jobs
    
    except Exception as e:
        print(f"Error scraping page {page_num}: {str(e)}")
        return None

def scrape_shine_jobs(base_url, max_pages=50, target_jobs=1000):
    """Main scraping function with pagination"""
    all_jobs = []
    page_num = 1
    duplicate_count = 0
    max_duplicates = 3  # Stop if we get too many duplicate pages
    
    while len(all_jobs) < target_jobs and page_num <= max_pages and duplicate_count < max_duplicates:
        jobs = scrape_page(base_url, page_num)
        
        if not jobs:
            duplicate_count += 1
            print(f"No jobs found on page {page_num} (duplicate count: {duplicate_count})")
        else:
            # Check if this page is a duplicate of the previous one
            if all_jobs and all(job in all_jobs[-len(jobs):] for job in jobs):
                duplicate_count += 1
                print(f"Duplicate page detected ({duplicate_count}/{max_duplicates})")
            else:
                duplicate_count = 0
                all_jobs.extend(jobs)
        
        print(f"Total jobs collected: {len(all_jobs)}")
        
        # Random delay to avoid being blocked
        delay = random.uniform(2, 5)
        time.sleep(delay)
        page_num += 1
    
    # Remove duplicates based on URL
    unique_jobs = []
    seen_urls = set()
    for job in all_jobs:
        if job['URL'] and job['URL'] not in seen_urls:
            seen_urls.add(job['URL'])
            unique_jobs.append(job)
    
    return unique_jobs[:target_jobs]

def save_to_csv(jobs, filename):
    """Save jobs data to CSV file"""
    df = pd.DataFrame(jobs)
    
    # Clean data
    df['Experience'] = df['Experience'].str.replace('Yrs', 'Years', regex=False)
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} jobs to {filename}")

if __name__ == "__main__":
    # Target URL for Software Engineer Fresher jobs with 0-4 years experience
    target_url = "https://www.shine.com/job-search/software-engineer-fresher-jobs?q=software-engineer-fresher&qActual=Software+Engineer+Fresher%2C+&minexp=4"
    
    print("Starting Shine.com job scraping...")
    jobs_data = scrape_shine_jobs(target_url, max_pages=100, target_jobs=1000)
    
    if jobs_data:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shine_software_engineer_fresher_jobs_{timestamp}.csv"
        
        save_to_csv(jobs_data, filename)
        print("Scraping completed successfully!")
    else:
        print("No jobs were scraped. Please check the URL or try again later.")