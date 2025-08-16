import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class BatchWorkdayScraper:
    def __init__(self):
        """Initialize the scraper"""
        self.jobs_data = []
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10)
    
    def login_and_navigate(self):
        """Handle login and navigation"""
        print("Opening Brown Workday login page...")
        self.driver.get("https://wd5.myworkday.com/brown/login.flex")
        
        print("\n" + "="*50)
        print("MANUAL STEPS:")
        print("1. Log in")
        print("2. Navigate to job listings")
        print("3. Search for '2025' to get 312 jobs")
        print("="*50)
        
        input("\nPress ENTER after searching for '2025'...")
        
        if "1422$7750" not in self.driver.current_url:
            self.driver.get("https://wd5.myworkday.com/brown/d/task/1422$7750.htmld")
            time.sleep(5)
    
    def scroll_until_count(self, target_count):
        """Scroll until we have at least target_count jobs visible"""
        selector = "div[data-automation-id='promptOption']"
        last_count = 0
        
        for _ in range(20):  # Max 20 scrolls
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            current_count = len(elements) - 1 if len(elements) > 0 else 0
            
            if current_count >= target_count:
                return current_count
            
            if current_count == last_count:
                return current_count
            
            last_count = current_count
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
        
        return last_count
    
    def scrape_job_page(self):
        """Extract job details quickly"""
        job_data = {
            'url': self.driver.current_url,
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            full_text = self.driver.find_element(By.TAG_NAME, "main").text
        except:
            full_text = self.driver.find_element(By.TAG_NAME, "body").text
        
        job_data['full_text'] = full_text
        lines = full_text.split('\n')
        
        # Quick extraction
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1]
            
            if line == 'Job Posting Title:':
                job_data['job_title'] = next_line
            elif line == 'Job Description:':
                job_data['job_description'] = next_line
            elif line == 'Recruiting Start Date:':
                job_data['recruiting_start_date'] = next_line
            elif line == 'Location' and 'location' not in job_data:
                job_data['location'] = next_line
            elif line == 'Department:':
                job_data['department'] = next_line
            elif line == 'Scheduled Weekly Hours:':
                job_data['scheduled_weekly_hours'] = next_line
            elif line == 'Hourly Rate:':
                job_data['hourly_range'] = next_line
            elif line == 'Hourly Range:':
                for j in range(i+1, min(i+7, len(lines))):
                    if lines[j] == 'Minimum:' and j + 1 < len(lines):
                        min_val = lines[j + 1]
                    elif lines[j] == 'Maximum:' and j + 1 < len(lines):
                        max_val = lines[j + 1]
                        job_data['hourly_range'] = f"${min_val} - ${max_val}"
                        break
        
        if 'job_title' not in job_data and len(lines) > 3:
            job_data['job_title'] = lines[2]
        
        return job_data
    
    def scrape_batch(self, start_index, batch_size=40):
        """Scrape a batch of jobs"""
        selector = "div[data-automation-id='promptOption']"
        scraped_in_batch = 0
        
        print(f"\n--- Batch starting at job {start_index + 1} ---")
        
        # Make sure enough jobs are loaded
        print(f"Scrolling to load jobs {start_index + 1} to {start_index + batch_size}...")
        self.scroll_until_count(start_index + batch_size + 1)
        
        for i in range(batch_size):
            job_index = start_index + i
            
            # Re-find elements
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if len(elements) > 1:
                elements = elements[1:]  # Skip header
            
            if job_index >= len(elements):
                print(f"  Job {job_index + 1}: Not found (reached end)")
                break
            
            # Scroll to and click job
            self.driver.execute_script("arguments[0].scrollIntoView(true);", elements[job_index])
            time.sleep(0.3)
            
            preview = elements[job_index].text[:50] if elements[job_index].text else ""
            print(f"  [{job_index + 1}] {preview}...")
            
            try:
                elements[job_index].click()
            except:
                self.driver.execute_script("arguments[0].click();", elements[job_index])
            
            time.sleep(3)
            
            # Check if we navigated
            if "1422$7750" not in self.driver.current_url:
                job_data = self.scrape_job_page()
                job_data['index'] = job_index + 1
                job_data['preview'] = preview
                
                self.jobs_data.append(job_data)
                scraped_in_batch += 1
                
                title = job_data.get('job_title', 'Unknown')[:30]
                print(f"    ✓ {title}")
                
                # Go back
                self.driver.back()
                time.sleep(2)
            else:
                print(f"    ✗ Failed to navigate")
        
        return scraped_in_batch
    
    def scrape_all_in_batches(self, total_target=312):
        """Scrape all jobs in batches of 40"""
        print(f"\n{'='*50}")
        print(f"SCRAPING {total_target} JOBS IN BATCHES")
        print(f"{'='*50}")
        
        start_time = time.time()
        batch_size = 40
        jobs_scraped = 0
        
        while jobs_scraped < total_target:
            # Scrape next batch
            scraped = self.scrape_batch(jobs_scraped, batch_size)
            jobs_scraped += scraped
            
            print(f"\nTotal scraped so far: {jobs_scraped}/{total_target}")
            
            if scraped == 0:
                print("No jobs scraped in last batch. Stopping.")
                break
            
            # Save backup
            if jobs_scraped % 50 == 0 or jobs_scraped >= total_target:
                self.save_to_json(f"backup_{jobs_scraped}.json")
                print(f"💾 Backup saved")
            
            # Check if we're done
            if jobs_scraped >= total_target:
                print(f"\n✅ Target reached: {jobs_scraped} jobs!")
                break
            
            # Reload the page every 2 batches to reset
            if jobs_scraped % 80 == 0:
                print("\nRefreshing page...")
                self.driver.get("https://wd5.myworkday.com/brown/d/task/1422$7750.htmld")
                time.sleep(3)
                print("Re-apply the '2025' filter if needed")
                input("Press ENTER when ready...")
        
        total_time = time.time() - start_time
        print(f"\nCompleted in {total_time/60:.1f} minutes")
        print(f"Average: {total_time/max(jobs_scraped,1):.1f} seconds per job")
    
    def save_to_json(self, filename="jobs.json"):
        """Save data to JSON"""
        output = {
            "metadata": {
                "scrape_date": datetime.now().isoformat(),
                "total_jobs": len(self.jobs_data),
                "source": "Brown Workday"
            },
            "jobs": self.jobs_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved to {filename}")
    
    def cleanup(self):
        """Close browser"""
        self.driver.quit()


if __name__ == "__main__":
    print("BATCH WORKDAY SCRAPER")
    print("This scrapes jobs in batches of 40")
    print("-" * 50)
    
    scraper = BatchWorkdayScraper()
    
    try:
        scraper.login_and_navigate()
        scraper.scrape_all_in_batches(total_target=312)
        scraper.save_to_json("brown_jobs_2025_final.json")
        
        print(f"\n{'='*50}")
        print(f"COMPLETE! Scraped {len(scraper.jobs_data)} jobs")
        print(f"Saved to: brown_jobs_2025_final.json")
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving...")
        scraper.save_to_json("brown_jobs_partial.json")
    
    except Exception as e:
        print(f"\nError: {e}")
        scraper.save_to_json("brown_jobs_error.json")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.cleanup()