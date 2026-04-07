// Dashboard JavaScript for Realtime Automation Dashboard

// DOM elements
const totalTestsElement = document.getElementById('total-tests');
const passedTestsElement = document.getElementById('passed-tests');
const failedTestsElement = document.getElementById('failed-tests');
const passRateElement = document.getElementById('pass-rate');
const autoRefreshButton = document.getElementById('auto-refresh-toggle');
const liveIndicator = document.getElementById('live-indicator');
const lastUpdatedElement = document.getElementById('last-updated');
const webTestsElement = document.getElementById('web-tests');
const mobileTestsElement = document.getElementById('mobile-tests');
const apiTestsElement = document.getElementById('api-tests');
const historyListElement = document.getElementById('history-list');

// State
let autoRefreshEnabled = localStorage.getItem('autoRefresh') !== 'false';
let expandedTests = {};
let refreshInterval;
let testExecutionInterval;
let currentTestStatus = {
    web: 'ready',
    mobile: 'ready', 
    api: 'ready'
};

// Initialize data
function initializeData() {
    // Update last updated time
    updateLastUpdated();
    
    // Set up auto-refresh if enabled
    if (autoRefreshEnabled) {
        startAutoRefresh();
        autoRefreshButton.classList.add('active');
        liveIndicator.style.display = 'inline-block';
    } else {
        liveIndicator.style.display = 'none';
    }
    
    // Add event listeners
    setupEventListeners();
    
    // Load available tests
    loadAvailableTests();
    
    // Animate cards on load
    setTimeout(() => {
        document.querySelectorAll('.summary-card').forEach((card, i) => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    }, 100);
}

// Setup event listeners
function setupEventListeners() {
    // Toggle auto-refresh
    autoRefreshButton.addEventListener('click', () => {
        autoRefreshEnabled = !autoRefreshEnabled;
        localStorage.setItem('autoRefresh', autoRefreshEnabled);
        
        if (autoRefreshEnabled) {
            autoRefreshButton.classList.add('active');
            liveIndicator.style.display = 'inline-block';
            startAutoRefresh();
        } else {
            autoRefreshButton.classList.remove('active');
            liveIndicator.style.display = 'none';
            clearInterval(refreshInterval);
        }
    });
    
    // Test execution buttons
    document.addEventListener('click', (e) => {
        // Run test buttons
        if (e.target.closest('.run-btn')) {
            const button = e.target.closest('.run-btn');
            const suite = button.dataset.suite;
            const headless = button.dataset.headless === 'true';
            const testName = document.getElementById('test-select').value;
            
            runTestSuite(suite, testName, headless);
        }
        
        // Stop test buttons
        if (e.target.closest('.stop-btn')) {
            const button = e.target.closest('.stop-btn');
            const suite = button.dataset.suite;
            
            stopTestSuite(suite);
        }
        
        // Toggle test details
        if (e.target.closest('.action-button')) {
            const button = e.target.closest('.action-button');
            const category = button.dataset.category;
            const index = parseInt(button.dataset.index);
            
            toggleTestDetails(category, index);
        }
        
        if (e.target.closest('.test-name')) {
            const testName = e.target.closest('.test-name');
            const row = testName.closest('.test-case-row');
            const category = row.parentElement.id.replace('-tests', '');
            const index = Array.from(row.parentElement.children).indexOf(row);
            
            toggleTestDetails(category, index);
        }
    });
}

// Toggle test details
function toggleTestDetails(category, index) {
    const key = `${category}-${index}`;
    const tbody = document.getElementById(`${category}-tests`);
    const rows = tbody.querySelectorAll('.test-case-row');
    const targetRow = rows[index];
    
    if (!targetRow) return;
    
    let nextSibling = targetRow.nextElementSibling;
    
    // Toggle arrow direction
    const arrow = targetRow.querySelector('.arrow');
    if (arrow) {
        arrow.textContent = expandedTests[key] ? '▶' : '▼';
    }
    
    // Toggle step rows
    while (nextSibling && nextSibling.classList.contains('step-row')) {
        nextSibling.classList.toggle('hidden');
        nextSibling = nextSibling.nextElementSibling;
    }
    
    // Update state
    expandedTests[key] = !expandedTests[key];
}

// Start auto-refresh
function startAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
        location.reload();
    }, 30000);
}

// Update last updated time
function updateLastUpdated() {
    const now = new Date();
    lastUpdatedElement.textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

// Test Execution Functions
function loadAvailableTests() {
    fetch('/api/available-tests')
        .then(response => response.json())
        .then(data => {
            const testSelect = document.getElementById('test-select');
            testSelect.innerHTML = '<option value="">All Tests</option>';
            
            // Add tests to dropdown
            Object.keys(data).forEach(suite => {
                data[suite].forEach(test => {
                    const option = document.createElement('option');
                    option.value = test.name;
                    option.textContent = `${suite.toUpperCase()}: ${test.name}`;
                    testSelect.appendChild(option);
                });
            });
        })
        .catch(error => {
            console.error('Error loading available tests:', error);
        });
}

function runTestSuite(suite, testName, headless) {
    console.log(`Running ${suite} tests...`);
    
    // Update UI
    updateTestStatus(suite, 'running');
    updateTestButtons(suite, true);
    
    // Make API call
    fetch('/api/run-test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            suite_type: suite,
            test_name: testName || null,
            headless: headless
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Test started:', data);
        
        // Start monitoring test status
        startTestMonitoring(suite);
    })
    .catch(error => {
        console.error('Error starting test:', error);
        updateTestStatus(suite, 'failed');
        updateTestButtons(suite, false);
    });
}

function stopTestSuite(suite) {
    console.log(`Stopping ${suite} tests...`);
    
    fetch(`/api/stop-test/${suite}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log('Test stopped:', data);
        updateTestStatus(suite, 'stopped');
        updateTestButtons(suite, false);
    })
    .catch(error => {
        console.error('Error stopping test:', error);
    });
}

function startTestMonitoring(suite) {
    // Clear existing interval
    if (testExecutionInterval) {
        clearInterval(testExecutionInterval);
    }
    
    // Start monitoring
    testExecutionInterval = setInterval(() => {
        checkTestStatus(suite);
    }, 2000);
}

function checkTestStatus(suite) {
    fetch(`/api/test-status/${suite}`)
        .then(response => response.json())
        .then(data => {
            console.log(`Test status for ${suite}:`, data);
            
            if (data.status === 'completed' || data.status === 'failed' || data.status === 'error') {
                // Test finished
                clearInterval(testExecutionInterval);
                updateTestStatus(suite, data.status);
                updateTestButtons(suite, false);
                
                // Refresh results if auto-refresh is enabled
                if (autoRefreshEnabled) {
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                }
            } else if (data.status === 'running') {
                updateTestStatus(suite, 'running');
            }
        })
        .catch(error => {
            console.error('Error checking test status:', error);
        });
}

function updateTestStatus(suite, status) {
    const statusElement = document.getElementById(`${suite}-status`);
    if (statusElement) {
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusElement.className = `test-status ${status}`;
    }
    
    currentTestStatus[suite] = status;
}

function updateTestButtons(suite, isRunning) {
    const runButtons = document.querySelectorAll(`[data-suite="${suite}"].run-btn`);
    const stopButton = document.querySelector(`[data-suite="${suite}"].stop-btn`);
    
    runButtons.forEach(btn => {
        btn.disabled = isRunning;
    });
    
    if (stopButton) {
        stopButton.disabled = !isRunning;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeData);
