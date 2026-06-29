/**
 * Clinical Treatment Outcome Prediction, Frontend Logic
 *
 * Handles:
 * - Form submission to /predict API
 * - Animated circle gauge rendering
 * - Score interpretation display
 * - Error handling
 */

// --- Configuration ---
// ARCHITECTURE:
// 1. Production/Docker: Nginx Reverse Proxy maps /api -> Inference Service.
// 2. Local Dev (Bare Metal): Frontend (8080) talks directly to API (8000) via CORS.
const getApiUrl = () => {
    if (window.location.hostname === 'localhost' && window.location.port === '8080') {
        return 'http://localhost:8000';
    }
    return '/api';
};

const API_BASE_URL = getApiUrl();

// --- DOM Elements ---
const form = document.getElementById('prediction-form');
const submitBtn = document.getElementById('submit-btn');
const btnLoader = document.getElementById('btn-loader');
const emptyState = document.getElementById('empty-state');
const resultContent = document.getElementById('result-content');
const errorState = document.getElementById('error-state');
const errorMessage = document.getElementById('error-message');
const scoreNumber = document.getElementById('score-number');
const circleProgress = document.getElementById('circle-progress');
const resultPatientId = document.getElementById('result-patient-id');
const modelVersion = document.getElementById('model-version');
const interpretationDot = document.getElementById('interpretation-dot');
const interpretationText = document.getElementById('interpretation-text');
const scoreInterpretation = document.getElementById('score-interpretation');
const validationToast = document.getElementById('validation-toast');
const validationMessage = document.getElementById('validation-message');

// Global variable to store valid combinations
let validCombinations = [];

// Circle constants
const CIRCLE_RADIUS = 85;
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS; // ~534.07

/**
 * Get score interpretation based on value
 */
function getInterpretation(score) {
    if (score < 4) return { text: 'Low improvement', level: 'low' };
    if (score < 7) return { text: 'Moderate improvement', level: 'medium' };
    return { text: 'High improvement', level: 'high' };
}

/**
 * Animate the score number counting up
 */
function animateScore(targetScore) {
    const duration = 1500;
    const startTime = performance.now();
    const startScore = 0;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const currentScore = startScore + (targetScore - startScore) * eased;

        scoreNumber.textContent = currentScore.toFixed(1);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Set the circle progress based on score (0-10)
 */
function setCircleProgress(score) {
    const percentage = score / 10;
    const offset = CIRCLE_CIRCUMFERENCE * (1 - percentage);
    circleProgress.style.strokeDashoffset = offset;
}

/**
 * Update the score circle's stroke color based on score
 */
function updateCircleColor(score) {
    if (score < 4) {
        circleProgress.style.stroke = '#ef4444';
    } else if (score < 7) {
        circleProgress.style.stroke = '#f59e0b';
    } else {
        circleProgress.style.stroke = '#6366f1';
    }
}

/**
 * Show result state
 */
function showResult(data) {
    emptyState.style.display = 'none';
    errorState.style.display = 'none';
    resultContent.style.display = 'flex';

    // Reset circle
    circleProgress.style.transition = 'none';
    circleProgress.style.strokeDashoffset = CIRCLE_CIRCUMFERENCE;

    // Set patient info
    resultPatientId.textContent = data.Patient_ID;
    modelVersion.textContent = data.model_version;

    // Score interpretation
    const interp = getInterpretation(data.Improvement_Score);
    interpretationText.textContent = interp.text;
    scoreInterpretation.className = `score-interpretation score-${interp.level}`;

    // Update colors
    updateCircleColor(data.Improvement_Score);

    // Trigger animation after a brief delay
    requestAnimationFrame(() => {
        circleProgress.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
        setCircleProgress(data.Improvement_Score);
        animateScore(data.Improvement_Score);
    });
}

/**
 * Show error state
 */
function showError(message) {
    emptyState.style.display = 'none';
    resultContent.style.display = 'none';
    errorState.style.display = 'flex';
    errorMessage.textContent = message;
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    if (isLoading) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
    } else {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

// --- Dropdown Population ---
async function fetchDropdowns() {
    try {
        const response = await fetch(`${API_BASE_URL}/dropdown-values`);
        if (!response.ok) throw new Error("Failed to fetch dropdown values");

        const data = await response.json();

        populateSelect('gender', data.genders);
        populateSelect('condition', data.conditions);
        populateSelect('drug-name', data.drugs);
        populateSelect('side-effects', data.side_effects);
        populateSelect('dosage', data.dosages);

        // Store valid combinations
        validCombinations = data.valid_combinations || [];

    } catch (err) {
        console.error("Error loading dropdowns:", err);
        showError("Failed to load form options. Please ensure API is running.");
    }
}

function populateSelect(id, values) {
    const select = document.getElementById(id);

    values.forEach(val => {
        const option = document.createElement('option');
        option.value = val;
        option.textContent = val;
        select.appendChild(option);
    });
}

// Initialize
fetchDropdowns();

// --- Validation Logic ---
function validateCombination() {
    const condition = document.getElementById('condition').value;
    const drugName = document.getElementById('drug-name').value;
    const dosage = document.getElementById('dosage').value;
    const sideEffects = document.getElementById('side-effects').value;

    // Only validate if all 4 are selected
    if (!condition || !drugName || !dosage || !sideEffects) {
        validationToast.style.display = 'none';
        submitBtn.disabled = false;
        return;
    }

    if (!validCombinations || validCombinations.length === 0) return;

    const dosageFloat = parseFloat(dosage);

    // Check if the exact combination exists
    const isValid = validCombinations.some(c =>
        c.Condition === condition &&
        c.Drug_Name === drugName &&
        c.Dosage_mg === dosageFloat &&
        c.Side_Effects === sideEffects
    );

    if (!isValid) {
        validationToast.style.display = 'flex';
        validationMessage.textContent = `Invalid Combination: '${condition}' treated with '${drugName}' (${dosageFloat}mg) causing '${sideEffects}' is not clinically recorded in the dataset.`;
        submitBtn.disabled = true;
    } else {
        validationToast.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Add event listeners for live validation
['condition', 'drug-name', 'dosage', 'side-effects'].forEach(id => {
    document.getElementById(id).addEventListener('change', validateCombination);
});

/**
 * Handle form submission
 */
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setLoading(true);

    // Double check validation on submit just in case
    validateCombination();
    if (submitBtn.disabled) {
        setLoading(false);
        return;
    }

    const payload = {
        Patient_ID: document.getElementById('patient-id').value.trim(),
        Age: parseInt(document.getElementById('age').value, 10),
        Gender: document.getElementById('gender').value,
        Condition: document.getElementById('condition').value,
        Drug_Name: document.getElementById('drug-name').value,
        Dosage_mg: parseFloat(document.getElementById('dosage').value),
        Treatment_Duration_days: parseInt(document.getElementById('duration').value, 10),
        Side_Effects: document.getElementById('side-effects').value,
    };

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();
        showResult(data);
    } catch (err) {
        console.error('Prediction error:', err);
        showError(err.message || 'Failed to connect to the prediction API');
    } finally {
        setLoading(false);
    }
});
