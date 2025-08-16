import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

class OptimizedSingleJobScraper:
    def __init__(self, optimization_level="medium"):
        """
        Initialize scraper with different optimization levels
        
        Args:
            optimization_level: "none", "medium", "aggressive"
        """
        self.optimization_level = optimization_level
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        if optimization_level in ["medium", "aggressive"]:
            # Performance optimizations
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option('prefs', {
                'profile.default_content_setting_values': {
                    'images': 2,  # Disable images
                    'plugins': 2,  # Disable plugins
                    'popups': 2,  # Disable popups
                }
            })
        
        if optimization_level == "aggressive":
            # More aggressive optimizations
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.page_load_strategy = 'eager'  # Don't wait for all resources
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        
        # Set implicit wait
        if optimization_level == "aggressive":
            self.driver.implicitly_wait(0.5)
        else:
            self.driver.implicitly_wait(1)
        
        # Wait timeouts based on optimization level
        self.wait_timeouts = {
            "none": {"short": 2, "medium": 3, "long": 5},
            "medium": {"short": 1, "medium": 2, "long": 3},
            "aggressive": {"short": 0.5, "medium": 1, "long": 2}
        }[optimization_level]
        
        self.wait = WebDriverWait(self.driver, self.wait_timeouts["long"])
        self.timings = {}
    
    def login_and_navigate(self):
        """Handle login and navigation"""
        print("Opening Brown Workday login page...")
        self.driver.get("https://wd5.myworkday.com/brown/login.flex")
        
        print("\n" + "="*50)
        print("MANUAL LOGIN REQUIRED")
        print("="*50)
        input("\nPress ENTER when you're on the job listings page...")
        
        if "1422$7750" not in self.driver.current_url:
            print("Navigating to job listings...")
            self.driver.get("https://wd5.myworkday.com/brown/d/task/1422$7750.htmld")
            
            # Wait for job listings to appear
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-automation-id='promptOption']")
                ))
            except TimeoutException:
                print("Warning: Couldn't confirm job listings loaded")
    
    def extract_job_data_optimized(self):
        """Ultra-fast extraction using optimized parsing"""
        # Get text in one shot
        full_text = self.driver.find_element(By.TAG_NAME, "body").text
        
        # Pre-compile the data structure
        job_data = {
            'url': self.driver.current_url,
            'scraped_at': datetime.now().isoformat(),
            'job_title': None,
            'job_description': None,
            'recruiting_start_date': None,
            'location': None,
            'department': None,
            'scheduled_weekly_hours': None,
            'hourly_range': None
        }
        
        # Split once and iterate once
        lines = full_text.split('\n')
        lines_len = len(lines)
        
        i = 0
        while i < lines_len - 1:  # -1 because we look ahead
            line = lines[i]
            next_line = lines[i + 1] if i + 1 < lines_len else ""
            
            # Use simple string comparisons first (faster than 'in')
            if line == 'Job Posting Title:':
                job_data['job_title'] = next_line
                i += 2
                continue
            elif line == 'Job Description:':
                job_data['job_description'] = next_line
                i += 2
                continue
            elif line == 'Recruiting Start Date:':
                job_data['recruiting_start_date'] = next_line
                i += 2
                continue
            elif line == 'Location':
                if not job_data['location']:  # Only first occurrence
                    job_data['location'] = next_line
                i += 2
                continue
            elif line == 'Department:':
                job_data['department'] = next_line
                i += 2
                continue
            elif line == 'Scheduled Weekly Hours:':
                job_data['scheduled_weekly_hours'] = next_line
                i += 2
                continue
            elif line == 'Hourly Rate:':
                job_data['hourly_range'] = next_line
                i += 2
                continue
            elif line == 'Hourly Range:':
                # Look for min/max in next 6 lines max
                for j in range(i+1, min(i+7, lines_len-1)):
                    if lines[j] == 'Minimum:' and j + 1 < lines_len:
                        min_val = lines[j + 1]
                    elif lines[j] == 'Maximum:' and j + 1 < lines_len:
                        max_val = lines[j + 1]
                        job_data['hourly_range'] = f"${min_val} - ${max_val}"
                        break
                i += 7
                continue
            
            i += 1
        
        # Quick fallback for title
        if not job_data['job_title'] and lines_len > 3:
            job_data['job_title'] = lines[2]
        
        return job_data
    
    def scrape_single_job_optimized(self):
        """Scrape a single job with various optimizations"""
        print(f"\n{'='*50}")
        print(f"OPTIMIZATION LEVEL: {self.optimization_level.upper()}")
        print(f"{'='*50}")
        
        # Find elements
        start = time.time()
        elements = self.driver.find_elements(By.CSS_SELECTOR, "div[data-automation-id='promptOption']")
        self.timings['find_elements'] = time.time() - start
        
        if len(elements) < 2:
            print("ERROR: Need at least 2 elements")
            return None
        
        # Get the first real job (skip header)
        target_job = elements[1]
        preview = target_job.text[:60] if target_job.text else ""
        print(f"Target job: {preview}")
        
        # Click
        start = time.time()
        target_job.click()
        self.timings['click'] = time.time() - start
        
        # Wait for page load
        start = time.time()
        if self.optimization_level == "none":
            # Fixed wait
            time.sleep(2)
        elif self.optimization_level == "medium":
            # Wait for URL change
            try:
                self.wait.until(lambda driver: "1422$7750" not in driver.current_url)
            except TimeoutException:
                time.sleep(1)
        else:  # aggressive
            # Minimal wait - just for URL change
            try:
                WebDriverWait(self.driver, self.wait_timeouts["short"]).until(
                    lambda driver: "1422$7750" not in driver.current_url
                )
            except TimeoutException:
                time.sleep(0.5)
        self.timings['wait_for_page'] = time.time() - start
        
        # Extract data
        start = time.time()
        job_data = self.extract_job_data_optimized()
        job_data['preview'] = preview
        job_data['optimization_level'] = self.optimization_level
        job_data['extraction_time'] = time.time() - start
        self.timings['extract_data'] = job_data['extraction_time']
        
        # Go back
        start = time.time()
        self.driver.back()
        self.timings['go_back'] = time.time() - start
        
        # Wait after back
        start = time.time()
        if self.optimization_level == "none":
            time.sleep(1.5)
        elif self.optimization_level == "medium":
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-automation-id='promptOption']")
                ))
            except TimeoutException:
                time.sleep(0.5)
        else:  # aggressive
            # Minimal wait
            try:
                WebDriverWait(self.driver, self.wait_timeouts["short"]).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[data-automation-id='promptOption']")
                    )
                )
            except TimeoutException:
                pass  # Continue anyway
        self.timings['wait_after_back'] = time.time() - start
        
        # Calculate total
        self.timings['total'] = sum(self.timings.values())
        
        # Add timings to job data
        job_data['timings'] = self.timings
        
        return job_data
    
    def run_comparison_test(self):
        """Run tests with all optimization levels"""
        results = {}
        
        for level in ["none", "medium", "aggressive"]:
            print(f"\n{'='*50}")
            print(f"Testing with optimization: {level}")
            print(f"{'='*50}")
            
            # Change optimization level
            self.optimization_level = level
            self.wait_timeouts = {
                "none": {"short": 2, "medium": 3, "long": 5},
                "medium": {"short": 1, "medium": 2, "long": 3},
                "aggressive": {"short": 0.5, "medium": 1, "long": 2}
            }[level]
            
            # Reset timings
            self.timings = {}
            
            # Run test
            job_data = self.scrape_single_job_optimized()
            
            if job_data:
                results[level] = job_data
                print(f"\nTiming breakdown:")
                print(f"  Find elements:    {self.timings['find_elements']:.3f}s")
                print(f"  Click:           {self.timings['click']:.3f}s")
                print(f"  Wait for page:   {self.timings['wait_for_page']:.3f}s")
                print(f"  Extract data:    {self.timings['extract_data']:.3f}s")
                print(f"  Go back:         {self.timings['go_back']:.3f}s")
                print(f"  Wait after back: {self.timings['wait_after_back']:.3f}s")
                print(f"  ─────────────────────────")
                print(f"  TOTAL:           {self.timings['total']:.2f}s")
            
            # Small delay between tests
            time.sleep(1)
        
        return results
    
    def save_results(self, job_data, filename="optimized_job_data.json"):
        """Save job data and timing results to JSON"""
        # Create comprehensive output
        output = {
            "metadata": {
                "scrape_date": datetime.now().isoformat(),
                "optimization_level": self.optimization_level,
                "total_time": self.timings.get('total', 0),
                "url": job_data.get('url', '')
            },
            "timings": self.timings,
            "job_data": job_data,
            "projections": {
                "time_per_job": self.timings.get('total', 0),
                "estimated_time_517_jobs_minutes": (517 * self.timings.get('total', 0)) / 60,
                "estimated_time_517_jobs_hours": (517 * self.timings.get('total', 0)) / 3600
            }
        }
        
        # Save to JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Data saved to: {filename}")
        
        return output
    
    def print_summary(self, job_data):
        """Print extraction summary"""
        print(f"\n{'='*50}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*50}")
        
        fields = ['job_title', 'job_description', 'recruiting_start_date',
                  'location', 'department', 'scheduled_weekly_hours', 'hourly_range']
        
        for field in fields:
            value = job_data.get(field)
            if value:
                display = value[:80] + "..." if len(str(value)) > 80 else value
                print(f"{field}: {display}")
            else:
                print(f"{field}: NOT FOUND")
    
    def cleanup(self):
        """Close browser"""
        self.driver.quit()


if __name__ == "__main__":
    print("Optimized Single Job Scraper")
    print("="*50)
    
    print("\nChoose optimization level:")
    print("1. None (baseline - fixed waits)")
    print("2. Medium (smart waits)")
    print("3. Aggressive (minimal waits)")
    print("4. Compare all three")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "4":
        # Compare all levels
        scraper = OptimizedSingleJobScraper("none")
        
        try:
            scraper.login_and_navigate()
            results = scraper.run_comparison_test()
            
            # Save comparison results
            comparison_output = {
                "comparison_date": datetime.now().isoformat(),
                "results": results
            }
            
            with open("optimization_comparison.json", 'w', encoding='utf-8') as f:
                json.dump(comparison_output, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*50}")
            print("COMPARISON SUMMARY")
            print(f"{'='*50}")
            
            for level, data in results.items():
                total_time = data['timings']['total']
                est_minutes = (517 * total_time) / 60
                print(f"\n{level.upper()}:")
                print(f"  Time per job: {total_time:.2f}s")
                print(f"  Est. for 517 jobs: {est_minutes:.1f} minutes")
            
            print(f"\n✅ Comparison saved to: optimization_comparison.json")
            
        finally:
            scraper.cleanup()
    
    else:
        # Single test
        level_map = {"1": "none", "2": "medium", "3": "aggressive"}
        level = level_map.get(choice, "medium")
        
        scraper = OptimizedSingleJobScraper(level)
        
        try:
            scraper.login_and_navigate()
            
            # Run the test
            job_data = scraper.scrape_single_job_optimized()
            
            if job_data:
                # Print summary
                scraper.print_summary(job_data)
                
                # Save to JSON
                output = scraper.save_results(job_data, f"job_data_{level}.json")
                
                # Print projections
                print(f"\n{'='*50}")
                print("TIME PROJECTIONS")
                print(f"{'='*50}")
                print(f"Time for this job: {scraper.timings['total']:.2f}s")
                print(f"Estimated for 517 jobs: {output['projections']['estimated_time_517_jobs_minutes']:.1f} minutes")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            input("\nPress ENTER to close browser...")
            scraper.cleanup()