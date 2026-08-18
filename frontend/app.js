document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const form = document.getElementById('recommend-form');
    const descriptionInput = document.getElementById('description');
    const captionInput = document.getElementById('caption');
    const submitBtn = document.getElementById('submit-btn');
    const exampleBtn = document.getElementById('example-btn');
    
    const demoModeBadge = document.getElementById('demo-mode-badge');
    const emptyState = document.getElementById('empty-state');
    const errorCard = document.getElementById('error-card');
    const errorMessage = document.getElementById('error-message');
    const loadingState = document.getElementById('loading-state');
    const resultsContent = document.getElementById('results-content');
    
    // Result details
    const recTitle = document.getElementById('rec-title');
    const recDifficulty = document.getElementById('rec-difficulty');
    const recCategory = document.getElementById('rec-category');
    const recConfidence = document.getElementById('rec-confidence');
    const recWhyExplanation = document.getElementById('rec-why-explanation');
    
    const detectedInterestTopic = document.getElementById('detected-interest-topic');
    const detectedInterestConfidence = document.getElementById('detected-interest-confidence');
    const detectedInterestWhy = document.getElementById('detected-interest-why');
    
    const reviewDescription = document.getElementById('review-description');
    const reviewCaption = document.getElementById('review-caption');
    
    const alternativesContainer = document.getElementById('alternatives-container');
    const scoreTableBody = document.getElementById('score-table-body');
    const toggleReasoningBtn = document.getElementById('toggle-reasoning-btn');
    const reasoningContent = document.getElementById('reasoning-content');
    const interestPathContainer = document.getElementById('interest-path-container');

    // Collapsible Logic
    toggleReasoningBtn.addEventListener('click', () => {
        toggleReasoningBtn.classList.toggle('active');
        reasoningContent.classList.toggle('hidden');
    });

    // Populate Example
    exampleBtn.addEventListener('click', () => {
        descriptionInput.value = "A software developer is debugging a Java application late at night. After several hours, they finally discover the bug.";
        captionInput.value = "When your Java code finally works after 3 hours 😂";
        
        // Scroll to inputs smoothly
        descriptionInput.scrollIntoView({ behavior: 'smooth' });
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const description = descriptionInput.value.trim();
        const caption = captionInput.value.trim();
        
        if (!description && !caption) {
            showError("Please enter a Reel description or caption.");
            return;
        }

        // Hide results, error, empty state
        resultsContent.classList.add('hidden');
        errorCard.classList.add('hidden');
        emptyState.classList.add('hidden');
        
        // Reset and show loading state
        resetLoadingSteps();
        loadingState.classList.remove('hidden');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';

        try {
            // Trigger step 1
            activateStep('step-1');

            // Send request to API
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ description, caption })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Failed to retrieve recommendation from server.");
            }

            // Animate through remaining steps sequentially (200ms per step)
            await animateStepsAndShowResult(data);

        } catch (err) {
            console.error(err);
            loadingState.classList.add('hidden');
            showError(err.message || "An unexpected error occurred. Please try again.");
            emptyState.classList.remove('hidden');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-circle-play"></i> Analyze & Recommend';
        }
    });

    // Loading Step Animations
    function resetLoadingSteps() {
        const steps = ['step-1', 'step-2', 'step-3', 'step-4', 'step-5'];
        steps.forEach(id => {
            const el = document.getElementById(id);
            el.className = 'step';
        });
    }

    function activateStep(id) {
        const el = document.getElementById(id);
        el.className = 'step active';
    }

    function completeStep(id) {
        const el = document.getElementById(id);
        el.className = 'step done';
    }

    async function animateStepsAndShowResult(data) {
        const stepIds = ['step-1', 'step-2', 'step-3', 'step-4', 'step-5'];
        
        // Complete current active step 1
        completeStep('step-1');
        
        // Sequentially complete steps 2 through 5
        for (let i = 1; i < stepIds.length; i++) {
            activateStep(stepIds[i]);
            await new Promise(resolve => setTimeout(resolve, 220));
            completeStep(stepIds[i]);
        }
        
        // Give a tiny final delay for polish
        await new Promise(resolve => setTimeout(resolve, 150));
        
        // Hide loading and show results
        loadingState.classList.add('hidden');
        renderResults(data);
    }

    // Render Results on the Dashboard
    function renderResults(data) {
        // Toggle Demo/AI Mode Badge
        demoModeBadge.classList.remove('hidden');
        if (data.mode === 'fallback') {
            demoModeBadge.className = 'demo-badge fallback-mode';
            demoModeBadge.innerHTML = '<i class="fa-solid fa-bolt"></i> Demo Mode — Using local recommendation engine';
        } else {
            demoModeBadge.className = 'demo-badge ai-mode';
            demoModeBadge.innerHTML = '<i class="fa-solid fa-brain"></i> AI Mode — Powered by Gemini';
        }

        // 1. Current Reel Section
        reviewDescription.textContent = data.current_reel.description;
        reviewCaption.textContent = data.current_reel.caption;

        // 2. Interest Detected Card
        detectedInterestTopic.textContent = data.interest_detected.topic;
        detectedInterestConfidence.textContent = data.interest_detected.confidence;
        
        // Update detected confidence badge classes
        detectedInterestConfidence.className = `badge badge-outline`;
        
        // Evidence list
        detectedInterestWhy.innerHTML = '';
        data.why.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            detectedInterestWhy.appendChild(li);
        });

        // 2.5. Interest Path Visualization
        interestPathContainer.innerHTML = '';
        if (data.interest_path && data.interest_path.length > 0) {
            data.interest_path.forEach((step, index) => {
                const stepSpan = document.createElement('span');
                stepSpan.className = 'path-step';
                stepSpan.textContent = step;
                interestPathContainer.appendChild(stepSpan);
                
                if (index < data.interest_path.length - 1) {
                    const arrowSpan = document.createElement('span');
                    arrowSpan.className = 'path-arrow';
                    arrowSpan.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
                    interestPathContainer.appendChild(arrowSpan);
                }
            });
        }

        // 3. Recommended Tech Reel Card
        recTitle.textContent = data.recommended_tech_reel.title;
        recCategory.textContent = data.category;
        recConfidence.textContent = data.confidence;
        recWhyExplanation.textContent = data.why_this_recommendation;
        
        // Difficulty Badge
        recDifficulty.textContent = data.difficulty;
        recDifficulty.className = `badge badge-difficulty ${data.difficulty.toLowerCase()}`;

        // 4. Why Not Alternatives List
        alternativesContainer.innerHTML = '';
        if (data.why_not && data.why_not.length > 0) {
            data.why_not.forEach(alt => {
                const altDiv = document.createElement('div');
                altDiv.className = 'alt-item';
                
                const statusClass = alt.status.toLowerCase().replace(' ', '-');
                const statusIcon = alt.status === 'Rejected' ? 'fa-solid fa-circle-xmark' : 'fa-solid fa-circle-minus';
                
                altDiv.innerHTML = `
                    <div class="alt-title">${alt.title}</div>
                    <div><span class="alt-status ${statusClass}">${statusIcon} ${alt.status}</span></div>
                    <div class="alt-reason">${alt.reason}</div>
                `;
                alternativesContainer.appendChild(altDiv);
            });
        } else {
            alternativesContainer.innerHTML = '<p class="alt-reason">No alternative candidates evaluated.</p>';
        }

        // 5. Score Breakdown Table
        scoreTableBody.innerHTML = '';
        for (const [key, val] of Object.entries(data.score_breakdown)) {
            const row = document.createElement('tr');
            
            let maxVal = "";
            let pointsText = val;
            
            if (key === 'Interest Match') maxVal = "/ 40";
            else if (key === 'Educational Value') maxVal = "/ 25";
            else if (key === 'Career Relevance') maxVal = "/ 15";
            else if (key === 'Engagement Potential') maxVal = "/ 10";
            else if (key === 'Hype Penalty') {
                maxVal = "Penalty";
                pointsText = val > 0 ? `-${val}` : '0';
            }
            else if (key === 'Narrowness Penalty') {
                maxVal = "Penalty";
                pointsText = val > 0 ? `-${val}` : '0';
            }
            else if (key === 'Final Score') {
                maxVal = "/ 100";
            }
            
            row.innerHTML = `
                <td><strong>${key}</strong></td>
                <td>${maxVal}</td>
                <td><strong>${pointsText}</strong></td>
            `;
            scoreTableBody.appendChild(row);
        }

        // Show Results panel
        resultsContent.classList.remove('hidden');
        
        // Scroll results into view
        resultsContent.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorCard.classList.remove('hidden');
        errorCard.scrollIntoView({ behavior: 'smooth' });
    }
});
