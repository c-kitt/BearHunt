import json
import re
from collections import defaultdict
from typing import List, Dict, Any

class JobRecommender:
    def __init__(self, jobs_file='brown_jobs_2025_final.json'):
        with open(jobs_file, 'r') as f:
            data = json.load(f)
        self.jobs = data['jobs']
        self.departments = list(set(job.get('department', '') for job in self.jobs))
        self.departments.sort()
        
    def ask_preferences(self):
        print("🎯 BROWN JOB FINDER - Let's find your perfect job!")
        print("=" * 55)
        print("Answer a few quick questions to get personalized recommendations:\n")
        
        preferences = {}
        print("1. How many hours per week do you want to work?")
        print("   a) Light commitment (1-8 hours)")
        print("   b) Moderate commitment (9-15 hours)")  
        print("   c) Heavy commitment (16+ hours)")
        print("   d) I'm flexible")
        
        hours_choice = input("\nYour choice (a/b/c/d): ").lower().strip()
        hours_map = {
            'a': (1, 8), 'b': (9, 15), 'c': (16, 40), 'd': (0, 40)
        }
        preferences['hours_range'] = hours_map.get(hours_choice, (0, 40))
        print("\n2. What's your preferred hourly pay range?")
        print("   a) Budget-friendly ($15-16/hr)")
        print("   b) Fair wage ($16-17/hr)")
        print("   c) Premium pay ($17+/hr)")
        print("   d) Pay doesn't matter")
        
        pay_choice = input("\nYour choice (a/b/c/d): ").lower().strip()
        pay_map = {
            'a': (15, 16), 'b': (16, 17), 'c': (17, 25), 'd': (0, 25)
        }
        preferences['pay_range'] = pay_map.get(pay_choice, (0, 25))
        print("\n3. What type of work interests you most?")
        print("   a) Research (labs, data analysis, experiments)")
        print("   b) Teaching/Tutoring (helping other students)")
        print("   c) Administrative (office work, organization)")
        print("   d) Technical/IT (computers, web, software)")
        print("   e) Creative/Library (writing, media, books)")
        print("   f) I'm open to anything")
        
        type_choice = input("\nYour choice (a/b/c/d/e/f): ").lower().strip()
        type_map = {
            'a': 'research', 'b': 'teaching', 'c': 'administrative', 
            'd': 'technical', 'e': 'creative', 'f': 'any'
        }
        preferences['job_type'] = type_map.get(type_choice, 'any')
        print("\n4. What academic areas interest you? (Select multiple)")
        
        interest_categories = {
            "STEM & Sciences": {
                'a': ['biology', 'life sciences', 'neuroscience'],
                'b': ['chemistry', 'chemical'],
                'c': ['physics', 'astronomy'],
                'd': ['computer science', 'computational'],
                'e': ['engineering', 'applied'],
                'f': ['mathematics', 'statistics'],
                'g': ['earth', 'environmental', 'planetary'],
                'h': ['medicine', 'health', 'medical']
            },
            "Social Sciences & Humanities": {
                'i': ['psychology', 'cognitive'],
                'j': ['history', 'historical'],
                'k': ['english', 'literature', 'writing'],
                'l': ['philosophy', 'religious'],
                'm': ['sociology', 'anthropology'],
                'n': ['political science', 'international'],
                'o': ['economics', 'business'],
                'p': ['art', 'visual arts', 'studio'],
                'q': ['music', 'theatre', 'performing']
            },
            "Professional & Applied": {
                'r': ['education', 'teaching'],
                's': ['public health', 'community'],
                't': ['library', 'information'],
                'u': ['athletics', 'sports', 'recreation'],
                'v': ['administration', 'student services'],
                'w': ['research', 'institute', 'center']
            }
        }
        
        print("\n   📚 STEM & Sciences:")
        print("      a) Biology/Life Sciences    b) Chemistry           c) Physics/Astronomy")
        print("      d) Computer Science         e) Engineering         f) Math/Statistics")
        print("      g) Earth/Environmental      h) Medicine/Health")
        
        print("\n   🎭 Social Sciences & Humanities:")
        print("      i) Psychology              j) History             k) English/Literature")
        print("      l) Philosophy/Religion     m) Sociology/Anthro    n) Political Science")
        print("      o) Economics/Business      p) Art/Visual Arts     q) Music/Theatre")
        
        print("\n   🏛️  Professional & Applied:")
        print("      r) Education/Teaching      s) Public Health       t) Library/Info")
        print("      u) Athletics/Recreation    v) Administration      w) Research Centers")
        
        print("\n   x) I'm open to anything")
        
        selected_interests = input("\nEnter letters for your interests (e.g., 'a,d,i'): ").lower().strip()
        dept_keywords = []
        if 'x' not in selected_interests:
            selections = [s.strip() for s in selected_interests.split(',') if s.strip()]
            for category in interest_categories.values():
                for letter, keywords in category.items():
                    if letter in selections:
                        dept_keywords.extend(keywords)
        
        preferences['department_keywords'] = dept_keywords
        print("\n5. What's your experience level?")
        print("   a) Beginner (new to work/research)")
        print("   b) Some experience (done similar work before)")
        print("   c) Experienced (confident in my abilities)")
        
        exp_choice = input("\nYour choice (a/b/c): ").lower().strip()
        preferences['experience_level'] = exp_choice
        
        return preferences
    
    def calculate_job_score(self, job: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        score = 0
        max_score = 0
        hours_weight = 25
        max_score += hours_weight
        try:
            job_hours = int(job.get('scheduled_weekly_hours', '0'))
            pref_min, pref_max = preferences['hours_range']
            if pref_min <= job_hours <= pref_max:
                score += hours_weight
            elif job_hours < pref_min:
                penalty = min(hours_weight, (pref_min - job_hours) * 3)
                score += max(0, hours_weight - penalty)
            else:
                penalty = min(hours_weight, (job_hours - pref_max) * 2)
                score += max(0, hours_weight - penalty)
        except:
            score += hours_weight * 0.5
        
        pay_weight = 20
        max_score += pay_weight
        hourly_range = job.get('hourly_range', '$0 - $0')
        match = re.search(r'\$(\d+(?:\.\d+)?)', hourly_range)
        if match:
            job_min_pay = float(match.group(1))
            pref_min_pay, pref_max_pay = preferences['pay_range']
            if pref_min_pay <= job_min_pay <= pref_max_pay:
                score += pay_weight
            else:
                distance = min(abs(job_min_pay - pref_min_pay), abs(job_min_pay - pref_max_pay))
                score += max(0, pay_weight - (distance * 5))
        else:
            score += pay_weight * 0.5
        
        type_weight = 30
        max_score += type_weight
        job_title = job.get('job_title', '').lower()
        job_desc = job.get('job_description', '').lower()
        pref_type = preferences['job_type']
        
        if pref_type == 'any':
            score += type_weight * 0.7
        else:
            type_keywords = {
                'research': ['research', 'ra ', 'lab', 'experiment', 'data', 'analysis'],
                'teaching': ['teaching', 'tutor', 'ta ', 'grader', 'mentor', 'peer'],
                'administrative': ['admin', 'assistant', 'coordinator', 'clerk', 'office'],
                'technical': ['tech', 'it', 'computer', 'web', 'software', 'digital'],
                'creative': ['library', 'writing', 'media', 'creative', 'design', 'art']
            }
            
            keywords = type_keywords.get(pref_type, [])
            matches = sum(1 for keyword in keywords if keyword in job_title or keyword in job_desc)
            if matches > 0:
                score += type_weight * min(1.0, matches * 0.4)
            else:
                score += type_weight * 0.2
        
        dept_weight = 15
        max_score += dept_weight
        job_dept = job.get('department', '').lower()
        dept_keywords = preferences['department_keywords']
        
        if not dept_keywords:
            score += dept_weight * 0.7
        else:
            matches = sum(1 for keyword in dept_keywords if keyword in job_dept)
            if matches > 0:
                score += dept_weight
            else:
                score += dept_weight * 0.3
        
        exp_weight = 10
        max_score += exp_weight
        exp_level = preferences.get('experience_level', 'b')
        desc_text = (job.get('job_description', '') + ' ' + job.get('job_title', '')).lower()
        
        if exp_level == 'a':
            if any(word in desc_text for word in ['entry', 'beginner', 'training', 'learn']):
                score += exp_weight
            elif any(word in desc_text for word in ['experience required', 'advanced', 'expert']):
                score += exp_weight * 0.3
            else:
                score += exp_weight * 0.7
        elif exp_level == 'c':
            if any(word in desc_text for word in ['advanced', 'independent', 'leadership', 'manage']):
                score += exp_weight
            else:
                score += exp_weight * 0.8
        else:
            score += exp_weight * 0.8
        return (score / max_score) * 100 if max_score > 0 else 0
    
    def get_recommendations(self, preferences: Dict[str, Any], num_recommendations: int = 10) -> List[Dict[str, Any]]:
        scored_jobs = []
        
        for job in self.jobs:
            score = self.calculate_job_score(job, preferences)
            scored_jobs.append((score, job))
        scored_jobs.sort(key=lambda x: x[0], reverse=True)
        
        return [{'score': score, 'job': job} for score, job in scored_jobs[:num_recommendations]]
    
    def display_recommendations(self, recommendations: List[Dict[str, Any]]):
        print(f"\n🌟 YOUR TOP {len(recommendations)} JOB RECOMMENDATIONS")
        print("=" * 60)
        
        for i, rec in enumerate(recommendations, 1):
            job = rec['job']
            score = rec['score']
            
            print(f"\n#{i} - {job.get('job_title', 'Unknown Title')} (Match: {score:.0f}%)")
            print(f"📍 {job.get('department', 'Unknown Department')}")
            print(f"⏰ {job.get('scheduled_weekly_hours', '?')} hours/week")
            print(f"💰 {job.get('hourly_range', 'Pay not specified')}")
            print(f"🏢 {job.get('location', 'Location not specified')}")
            desc = job.get('job_description', '')
            if desc and len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"📝 {desc}")
            print(f"🔗 {job.get('url', '')}")
            
            if i < len(recommendations):
                print("-" * 40)
    
    def find_similar_jobs(self, selected_job: Dict[str, Any], num_similar: int = 5) -> List[Dict[str, Any]]:
        selected_dept = selected_job.get('department', '')
        selected_title = selected_job.get('job_title', '').lower()
        selected_hours = selected_job.get('scheduled_weekly_hours', '0')
        
        similar_jobs = []
        
        for job in self.jobs:
            if job == selected_job:
                continue
                
            similarity_score = 0
            
            if job.get('department', '') == selected_dept:
                similarity_score += 40
            
            job_title = job.get('job_title', '').lower()
            title_words = set(selected_title.split())
            job_title_words = set(job_title.split())
            common_words = title_words.intersection(job_title_words)
            similarity_score += len(common_words) * 10
            try:
                job_hours = int(job.get('scheduled_weekly_hours', '0'))
                selected_hours_int = int(selected_hours)
                hour_diff = abs(job_hours - selected_hours_int)
                if hour_diff <= 2:
                    similarity_score += 20
                elif hour_diff <= 5:
                    similarity_score += 10
            except:
                pass
            
            if similarity_score > 20:
                similar_jobs.append((similarity_score, job))
        similar_jobs.sort(key=lambda x: x[0], reverse=True)
        
        return [job for score, job in similar_jobs[:num_similar]]
    
    def interactive_session(self):
        preferences = self.ask_preferences()
        
        while True:
            recommendations = self.get_recommendations(preferences, 10)
            self.display_recommendations(recommendations)
            
            print(f"\n🔧 OPTIONS:")
            print("1. See more recommendations")
            print("2. Find jobs similar to one above (enter job number)")
            print("3. Adjust preferences")
            print("4. Exit")
            
            choice = input("\nWhat would you like to do? ").strip()
            
            if choice == '1':
                recommendations = self.get_recommendations(preferences, 20)
                self.display_recommendations(recommendations[10:])
                
            elif choice.isdigit():
                job_num = int(choice) - 1
                if 0 <= job_num < len(recommendations):
                    selected_job = recommendations[job_num]['job']
                    print(f"\n🔍 Finding jobs similar to: {selected_job.get('job_title', 'Unknown')}")
                    similar_jobs = self.find_similar_jobs(selected_job)
                    
                    if similar_jobs:
                        print(f"\n📋 SIMILAR JOBS:")
                        print("=" * 40)
                        for i, job in enumerate(similar_jobs, 1):
                            print(f"{i}. {job.get('job_title', 'Unknown')}")
                            print(f"   {job.get('department', 'Unknown Department')}")
                            print(f"   {job.get('scheduled_weekly_hours', '?')} hrs/week, {job.get('hourly_range', 'Pay TBD')}")
                            print()
                    else:
                        print("No similar jobs found.")
                else:
                    print("Invalid job number.")
                    
            elif choice == '3':
                preferences = self.ask_preferences()
                
            elif choice == '4':
                print("\n👋 Good luck with your job search!")
                break
                
            else:
                print("Invalid choice. Please try again.")

def main():
    try:
        recommender = JobRecommender()
        recommender.interactive_session()
    except FileNotFoundError:
        print("❌ Error: brown_jobs_2025_final.json not found!")
        print("Make sure the file is in the same directory as this script.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()