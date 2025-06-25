import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime
import os
from urllib.parse import urljoin
import json
from tqdm import tqdm

# Configure session with enhanced headers
session = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.shine.com/',
    'DNT': '1'
}
session.headers.update(HEADERS)

def scrape_job_details(job_url):
    """Scrape detailed information from individual job page"""
    try:
        response = session.get(job_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        details = {}
        
        # Extract key details
        job_details = soup.find('div', class_='jobdetailsNova_jobdetails__j8y_W') or {}
        
        # Key Highlights
        highlights = job_details.find('div', class_='jobdetailsNova_jdKeyHighlights__YxC7n')
        if highlights:
            for item in highlights.find_all('li'):
                text = item.get_text(strip=True)
                if 'Yrs' in text:
                    details['Experience'] = text.replace('Yrs', 'Years')
                elif any(x in text.lower() for x in ['salary', 'lpa', 'disclosed']):
                    details['Salary'] = text
                elif any(x in text.lower() for x in ['location', 'city', 'remote']):
                    details['Location'] = text
        
        # Job Description
        desc = job_details.find('div', class_='jobdetailsNova_jdJobDescription__6JHQZ')
        if desc:
            desc_text = desc.find('pre', class_='jobdetailsNova_jdJobTxt__ND51u')
            details['Description'] = desc_text.get_text(strip=True) if desc_text else None
        
        # Other Details (Role, Industry, etc.)
        other_details = job_details.find('div', class_='jobdetailsNova_jdOtherDetails__14Nht')
        if other_details:
            for item in other_details.find_all('li'):
                label = item.find('span', class_='jobdetailsNova_jdRole__xh4DN')
                value = item.find('strong', class_='jobdetailsNova_jdProduct___1Mk3')
                if label and value:
                    key = label.get_text(strip=True).replace(' ', '_').lower()
                    details[key] = value.get_text(strip=True)
        
        details['details_scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return details
    
    except Exception as e:
        print(f"Error scraping {job_url}: {str(e)}")
        return {}

def scrape_job_card(card):
    """Extract job details from a single job card"""
    job = {}
    try:
        # Basic info
        job['title'] = (card.find('p', class_='jobCardNova_bigCardTopTitleHeading__Rj2sC') or {}).get_text(strip=True)
        job['company'] = (card.find('span', class_='jobCardNova_bigCardTopTitleName__M_W_m') or {}).get_text(strip=True)
        
        # Location
        loc_elem = card.find('div', class_='jobCardNova_bigCardLocation__OMkI1')
        job['location'] = (loc_elem.find('div', class_='jobCardNova_bigCardCenterListLoc__usiPB') or {}).get_text(strip=True) if loc_elem else None
        
        # Experience and Salary
        job['experience'] = (card.find('span', class_='jobCardNova_bigCardCenterListExp__KTSEc') or {}).get_text(strip=True)
        job['salary'] = (card.find('div', class_='jobCardNova_bigCardSalary__XH5q_') or {}).get_text(strip=True)
        
        # Posted date and skills
        job['posted'] = (card.find('span', class_='jobCardNova_postedData__LTERc') or {}).get_text(strip=True)
        
        # Skills (both visible and tooltip)
        skills = []
        skills.extend([skill.get_text(strip=True) for skill in card.find_all('li', class_='jobCardNova_toolTip__MPK0n')])
        tooltip = card.find('div', class_='tooltipNova_tooltip__WGL5G')
        if tooltip:
            skills.extend([s.strip() for s in tooltip.get_text(strip=True).split(',')])
        job['skills'] = ', '.join(filter(None, skills)) if skills else None
        
        # URL and hiring status
        url_elem = card.find('meta', itemprop='url')
        job['url'] = url_elem['content'] if url_elem else None
        job['hiring_status'] = (card.find('div', class_='jobTypeTagNova_hiringTag__xiY4f') or {}).get_text(strip=True)
        
        job['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        print(f"Error parsing job card: {str(e)}")
    
    return job

def scrape_page(url, page_num, retries=3):
    """Scrape a single page of job listings"""
    for attempt in range(retries):
        try:
            paginated_url = f"{url}&page={page_num}"
            response = session.get(paginated_url, timeout=15)
            
            if response.status_code == 429:
                wait_time = (attempt + 1) * 30
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_='jobCardNova_bigCard__W2xn3')
            
            if not job_cards:
                return None
            
            return [scrape_job_card(card) for card in job_cards if card]
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep((attempt + 1) * 10)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            if attempt < retries - 1:
                time.sleep(5)
    
    return None

def scrape_shine_jobs(base_url, max_pages=500, target_jobs=20000, details_percentage=0.2):
    """Main scraping function optimized for your specific URL"""
    all_jobs = []
    page_num = 1
    duplicate_count = 0
    max_duplicates = 5
    
    os.makedirs('shine_jobs_data', exist_ok=True)
    
    # Progress tracking
    pbar = tqdm(total=target_jobs, desc="Scraping jobs")
    
    while len(all_jobs) < target_jobs and page_num <= max_pages and duplicate_count < max_duplicates:
        jobs = scrape_page(base_url, page_num)
        
        if not jobs:
            duplicate_count += 1
            page_num += 1
            time.sleep(random.uniform(5, 10))
            continue
        
        # Scrape details for a sample of jobs
        detailed_jobs = []
        sample_size = max(1, int(len(jobs) * details_percentage))
        for job in random.sample(jobs, sample_size):
            if job.get('url'):
                time.sleep(random.uniform(2, 4))
                details = scrape_job_details(job['url'])
                job.update(details)
                detailed_jobs.append(job)
        
        all_jobs.extend(detailed_jobs)
        pbar.update(len(detailed_jobs))
        
        # Save checkpoint every 20 pages
        if page_num % 20 == 0:
            checkpoint_file = f"shine_jobs_data/checkpoint_page_{page_num}.csv"
            save_to_csv(all_jobs, checkpoint_file)
            print(f"\nCheckpoint saved at page {page_num}")
        
        # Adaptive delay
        delay = random.uniform(5, 15) * (1 + duplicate_count * 0.5)
        time.sleep(delay)
        page_num += 1
        duplicate_count = 0 if jobs else duplicate_count + 1
    
    pbar.close()
    
    # Remove duplicates
    unique_jobs = []
    seen_urls = set()
    for job in all_jobs:
        if job.get('url') and job['url'] not in seen_urls:
            seen_urls.add(job['url'])
            unique_jobs.append(job)
    
    return unique_jobs[:target_jobs]

def save_to_csv(jobs, filename):
    """Save jobs data to CSV with proper formatting"""
    df = pd.DataFrame(jobs)
    
    # Clean date fields
    for col in ['posted', 'scraped_at', 'details_scraped_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Save with compression if large
    if len(df) > 10000:
        filename = filename.replace('.csv', '.gz')
        df.to_csv(filename, index=False, compression='gzip')
    else:
        df.to_csv(filename, index=False)
    
    print(f"Saved {len(df)} jobs to {filename}")

if __name__ == "__main__":
    # Your specific URL for data scientist/software engineer/graduate trainee jobs
    TARGET_URL = "https://www.shine.com/job-search/data-scientist-software-engineer-software-developer-graduate-trainee-jobs?q=data-scientist-software-engineer-software-developer-graduate-trainee&qActual=data%20scientist%20software%20engineer%20software%20developer%20graduate%20trainee&minexp=4&fexp=1&fexp=2"
    
    print("Starting specialized Shine.com job scraping...")
    print(f"Target URL: {TARGET_URL}")
    
    jobs_data = scrape_shine_jobs(
        TARGET_URL,
        max_pages=500,
        target_jobs=20000,
        details_percentage=0.15  # Lower percentage for this specific search
    )
    
    if jobs_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"shine_data_scientist_engineer_trainee_jobs_{timestamp}.csv"
        save_to_csv(jobs_data, filename)
        
        # Additional JSON output
        json_filename = filename.replace('.csv', '.json')
        with open(json_filename, 'w') as f:
            json.dump(jobs_data, f, indent=2)
        
        print(f"\nSuccessfully collected {len(jobs_data)} jobs!")
        print(f"CSV saved to: {filename}")
        print(f"JSON saved to: {json_filename}")
    else:
        print("No jobs were collected. Please check the URL or try again later.")