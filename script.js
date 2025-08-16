let jobs = [];
let currentRecommendations = [];
let userPreferences = {};
let currentPage = 0;
let currentStep = 1;
const jobsPerPage = 10;

fetch('data/brown_jobs_2025_final.json')
    .then(response => response.json())
    .then(data => {
        jobs = data.jobs;
    })
    .catch(error => {
        console.error('Error loading jobs:', error);
        alert('Error loading job data. Please make sure brown_jobs_2025_final.json is available.');
    });

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('option')) {
        const question = e.target.closest('.options').dataset.question;
        
        if (question === 'interests') {
            e.target.classList.toggle('selected');
            
            if (e.target.dataset.value === 'open' && e.target.classList.contains('selected')) {
                document.querySelectorAll('[data-question="interests"] .option').forEach(opt => {
                    if (opt !== e.target) opt.classList.remove('selected');
                });
            } else if (e.target.dataset.value !== 'open') {
                document.querySelector('[data-value="open"]').classList.remove('selected');
            }
        } else {
            e.target.closest('.options').querySelectorAll('.option').forEach(opt => {
                opt.classList.remove('selected');
            });
            e.target.classList.add('selected');
        }
        
        updateButtonState();
    }
});

function updateButtonState() {
    const currentQuestion = document.querySelector('.question.active');
    const button = currentQuestion.querySelector('.next-btn, .find-jobs-btn');
    const question = currentQuestion.querySelector('.options').dataset.question;
    
    let hasSelection = false;
    
    if (question === 'interests') {
        hasSelection = currentQuestion.querySelectorAll('.option.selected').length > 0;
    } else {
        hasSelection = currentQuestion.querySelector('.option.selected') !== null;
    }
    
    button.disabled = !hasSelection;
}

function nextQuestion() {
    if (currentStep < 4) {
        document.getElementById(`question${currentStep}`).classList.remove('active');
        currentStep++;
        document.getElementById(`question${currentStep}`).classList.add('active');
        document.getElementById('currentStep').textContent = currentStep;
        
        const progress = (currentStep / 4) * 100;
        document.getElementById('progress').style.width = progress + '%';
        
        updateButtonState();
    }
}

function getPreferences() {
    const preferences = {};
    
    const hoursSelected = document.querySelector('[data-question="hours"] .selected');
    if (hoursSelected) {
        const hoursMap = {
            'light': [1, 8],
            'moderate': [9, 15],
            'heavy': [16, 40],
            'flexible': [0, 40]
        };
        preferences.hoursRange = hoursMap[hoursSelected.dataset.value] || [0, 40];
    }

    const paySelected = document.querySelector('[data-question="pay"] .selected');
    if (paySelected) {
        const payMap = {
            'budget': [15, 16],
            'fair': [16, 17],
            'premium': [17, 25],
            'any': [0, 25]
        };
        preferences.payRange = payMap[paySelected.dataset.value] || [0, 25];
    }

    const workTypeSelected = document.querySelector('[data-question="workType"] .selected');
    if (workTypeSelected) {
        preferences.jobType = workTypeSelected.dataset.value;
    }

    const interestsSelected = document.querySelectorAll('[data-question="interests"] .selected');
    preferences.departmentKeywords = [];
    
    const interestKeywords = {
        'biology': ['biology', 'life sciences', 'neuroscience'],
        'chemistry': ['chemistry', 'chemical'],
        'physics': ['physics', 'astronomy'],
        'computer': ['computer science', 'computational'],
        'engineering': ['engineering', 'applied'],
        'math': ['mathematics', 'statistics'],
        'earth': ['earth', 'environmental', 'planetary'],
        'medicine': ['medicine', 'health', 'medical'],
        'psychology': ['psychology', 'cognitive'],
        'history': ['history', 'historical'],
        'english': ['english', 'literature', 'writing'],
        'philosophy': ['philosophy', 'religious'],
        'sociology': ['sociology', 'anthropology'],
        'political': ['political science', 'international'],
        'economics': ['economics', 'business'],
        'art': ['art', 'visual arts', 'studio'],
        'music': ['music', 'theatre', 'performing'],
        'education': ['education', 'teaching'],
        'health': ['public health', 'community'],
        'library': ['library', 'information'],
        'athletics': ['athletics', 'sports', 'recreation'],
        'administration': ['administration', 'student services'],
        'research': ['research', 'institute', 'center']
    };

    interestsSelected.forEach(option => {
        if (option.dataset.value !== 'open') {
            const keywords = interestKeywords[option.dataset.value] || [];
            preferences.departmentKeywords.push(...keywords);
        }
    });


    return preferences;
}

function calculateJobScore(job, preferences) {
    let score = 0;
    let maxScore = 0;

    const hoursWeight = 30;
    maxScore += hoursWeight;
    try {
        const jobHours = parseInt(job.scheduled_weekly_hours || '0');
        const [prefMin, prefMax] = preferences.hoursRange || [0, 40];
        if (prefMin <= jobHours && jobHours <= prefMax) {
            score += hoursWeight;
        } else if (jobHours < prefMin) {
            const penalty = Math.min(hoursWeight, (prefMin - jobHours) * 3);
            score += Math.max(0, hoursWeight - penalty);
        } else {
            const penalty = Math.min(hoursWeight, (jobHours - prefMax) * 2);
            score += Math.max(0, hoursWeight - penalty);
        }
    } catch {
        score += hoursWeight * 0.5;
    }

    const payWeight = 25;
    maxScore += payWeight;
    const hourlyRange = job.hourly_range || '$0 - $0';
    const match = hourlyRange.match(/\$(\d+(?:\.\d+)?)/);
    if (match) {
        const jobMinPay = parseFloat(match[1]);
        const [prefMinPay, prefMaxPay] = preferences.payRange || [0, 25];
        if (prefMinPay <= jobMinPay && jobMinPay <= prefMaxPay) {
            score += payWeight;
        } else {
            const distance = Math.min(Math.abs(jobMinPay - prefMinPay), Math.abs(jobMinPay - prefMaxPay));
            score += Math.max(0, payWeight - (distance * 5));
        }
    } else {
        score += payWeight * 0.5;
    }

    const typeWeight = 35;
    maxScore += typeWeight;
    const jobTitle = (job.job_title || '').toLowerCase();
    const jobDesc = (job.job_description || '').toLowerCase();
    const prefType = preferences.jobType;

    if (prefType === 'any') {
        score += typeWeight * 0.7;
    } else {
        const typeKeywords = {
            'research': ['research', 'ra ', 'lab', 'experiment', 'data', 'analysis'],
            'teaching': ['teaching', 'tutor', 'ta ', 'grader', 'mentor', 'peer'],
            'administrative': ['admin', 'assistant', 'coordinator', 'clerk', 'office'],
            'technical': ['tech', 'it', 'computer', 'web', 'software', 'digital'],
            'creative': ['library', 'writing', 'media', 'creative', 'design', 'art']
        };

        const keywords = typeKeywords[prefType] || [];
        const matches = keywords.filter(keyword => jobTitle.includes(keyword) || jobDesc.includes(keyword)).length;
        if (matches > 0) {
            score += typeWeight * Math.min(1.0, matches * 0.4);
        } else {
            score += typeWeight * 0.2;
        }
    }

    const deptWeight = 10;
    maxScore += deptWeight;
    const jobDept = (job.department || '').toLowerCase();
    const deptKeywords = preferences.departmentKeywords || [];

    if (deptKeywords.length === 0) {
        score += deptWeight * 0.7;
    } else {
        const matches = deptKeywords.filter(keyword => jobDept.includes(keyword)).length;
        if (matches > 0) {
            score += deptWeight;
        } else {
            score += deptWeight * 0.3;
        }
    }


    return maxScore > 0 ? (score / maxScore) * 100 : 0;
}

function findJobs() {
    userPreferences = getPreferences();
    
    if (jobs.length === 0) {
        alert('Job data is still loading. Please try again in a moment.');
        return;
    }

    const scoredJobs = jobs.map(job => ({
        job: job,
        score: calculateJobScore(job, userPreferences)
    }));

    scoredJobs.sort((a, b) => b.score - a.score);
    
    currentRecommendations = scoredJobs;
    currentPage = 0;
    
    document.getElementById('questionnaire').classList.add('hidden');
    document.getElementById('results').classList.remove('hidden');
    
    displayJobs();
}

function displayJobs() {
    const startIndex = currentPage * jobsPerPage;
    const endIndex = startIndex + jobsPerPage;
    const jobsToShow = currentRecommendations.slice(startIndex, endIndex);

    const jobList = document.getElementById('jobList');
    if (currentPage === 0) {
        jobList.innerHTML = '<h2>Your Top Job Recommendations</h2>';
    }

    jobsToShow.forEach((rec, index) => {
        const job = rec.job;
        const score = rec.score;
        const globalIndex = startIndex + index + 1;

        const jobCard = document.createElement('div');
        jobCard.className = 'job-card';
        jobCard.innerHTML = `
            <div class="match-score">${Math.round(score)}% match</div>
            <h3 class="job-title">#${globalIndex} - ${job.job_title || 'Unknown Title'}</h3>
            <div class="job-details">
                Department: ${job.department || 'Unknown Department'}<br>
                Hours: ${job.scheduled_weekly_hours || '?'} hours/week<br>
                Pay: ${job.hourly_range || 'Pay not specified'}<br>
                Location: ${job.location || 'Location not specified'}
            </div>
            <div class="job-description">
                Description: ${job.job_description ? (job.job_description.length > 200 ? job.job_description.substring(0, 200) + '...' : job.job_description) : 'No description available'}
            </div>
            <div>
                <a href="${job.url || '#'}" target="_blank">View Job Posting</a>
            </div>
            <button class="similar-btn" onclick="findSimilarJobs(${job.index})">Find Similar Jobs</button>
        `;
        jobList.appendChild(jobCard);
    });
}

function showMore() {
    currentPage++;
    displayJobs();
}

function findSimilarJobs(jobIndex) {
    const selectedJob = jobs.find(job => job.index === jobIndex);
    if (!selectedJob) return;

    const similarJobs = jobs.filter(job => {
        if (job.index === jobIndex) return false;
        
        let similarity = 0;
        
        if (job.department === selectedJob.department) {
            similarity += 40;
        }
        
        const selectedWords = new Set((selectedJob.job_title || '').toLowerCase().split(' '));
        const jobWords = new Set((job.job_title || '').toLowerCase().split(' '));
        const commonWords = [...selectedWords].filter(word => jobWords.has(word));
        similarity += commonWords.length * 10;
        
        return similarity > 20;
    }).slice(0, 5);

    if (similarJobs.length > 0) {
        const similarSection = document.createElement('div');
        similarSection.innerHTML = `
            <h3>Jobs similar to: ${selectedJob.job_title}</h3>
            ${similarJobs.map(job => `
                <div style="margin: 1rem 0; padding: 1rem; background: #f9f9f9; border-radius: 4px;">
                    <strong>${job.job_title}</strong><br>
                    ${job.department}<br>
                    ${job.scheduled_weekly_hours} hrs/week, ${job.hourly_range}
                </div>
            `).join('')}
        `;
        
        const allCards = document.querySelectorAll('.job-card');
        const targetCard = Array.from(allCards).find(card => 
            card.innerHTML.includes(`onclick="findSimilarJobs(${jobIndex})`)
        );
        if (targetCard) {
            targetCard.insertAdjacentElement('afterend', similarSection);
        }
    } else {
        alert('No similar jobs found.');
    }
}

function startOver() {
    currentPage = 0;
    currentStep = 1;
    currentRecommendations = [];
    userPreferences = {};
    
    document.querySelectorAll('.option.selected').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    document.querySelectorAll('.question').forEach(q => {
        q.classList.remove('active');
    });
    
    document.getElementById('question1').classList.add('active');
    document.getElementById('currentStep').textContent = '1';
    document.getElementById('progress').style.width = '25%';
    
    document.getElementById('questionnaire').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
    
    updateButtonState();
}