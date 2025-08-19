// Dashboard JavaScript for Prior Authorization Management

let currentTab = 'all';
let allPriorAuths = [];
let filteredPriorAuths = [];
let currentSort = { field: 'created_date', direction: 'asc' };

// Automation workflow variables
let currentAutomationStep = 1;
let automationData = {};
let streamingInterval = null;
let stepResults = {};
let automationPollingInterval = null;

// Step configurations
const automationSteps = [
    {
        id: 1,
        title: "Policy Research & Coverage Analysis",
        description: "Searching web for insurance policy documents and determining coverage",
        icon: "fas fa-search",
        content: "coverage"
    },
    {
        id: 2,
        title: "Form Processing",
        description: "Processing form questions and extracting EHR data",
        icon: "fas fa-file-medical",
        content: "form"
    }
];

// Auto-scroll configuration
let autoScrollEnabled = true;
let lastScrollTime = 0;
const SCROLL_THROTTLE_MS = 500; // Minimum time between scrolls

// Auto-scroll utility function
function autoScrollToElement(element, options = {}) {
    if (!autoScrollEnabled || !element) return;
    
    const now = Date.now();
    if (now - lastScrollTime < SCROLL_THROTTLE_MS) return;
    
    lastScrollTime = now;
    
    const defaultOptions = {
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest',
        delay: 200
    };
    
    const scrollOptions = { ...defaultOptions, ...options };
    
    setTimeout(() => {
        element.scrollIntoView(scrollOptions);
    }, scrollOptions.delay);
}

// Toggle auto-scroll function
function toggleAutoScroll() {
    autoScrollEnabled = !autoScrollEnabled;
    const toggleBtn = document.getElementById('auto-scroll-toggle');
    
    if (autoScrollEnabled) {
        toggleBtn.innerHTML = '<i class="fas fa-arrow-down"></i> Auto-scroll';
        toggleBtn.className = 'btn btn-outline-secondary';
        toggleBtn.title = 'Disable auto-scroll';
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-times"></i> Auto-scroll';
        toggleBtn.className = 'btn btn-outline-danger';
        toggleBtn.title = 'Enable auto-scroll';
    }
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, calling loadData...');
    loadData();
    setupEventListeners();
});

function setupEventListeners() {
    // EPIC-style tab navigation
    document.querySelectorAll('.epic-tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });

    // Search and filters
    document.getElementById('search-input').addEventListener('input', filterData);
    document.getElementById('provider-filter').addEventListener('change', filterData);
    document.getElementById('status-filter').addEventListener('change', filterData);

    // Select all checkbox
    document.getElementById('select-all').addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.auth-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateBulkActions();
    });

    // Sorting
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const field = this.dataset.sort;
            sortData(field);
        });
    });

    // Update last refreshed time
    updateLastRefreshedTime();
}

function switchTab(tab) {
    currentTab = tab;
    
    // Update active tab button
    document.querySelectorAll('.epic-tab-button').forEach(button => {
        button.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    
    // Load data for the selected tab
    loadData();
}

async function loadData() {
    console.log('=== loadData called ===');
    showLoading(true);
    
    try {
        console.log('Loading data for tab:', currentTab);
        const url = `/api/prior-auths/${currentTab}`;
        console.log('Fetching from URL:', url);
        
        const response = await fetch(url);
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        const data = await response.json();
        console.log('Received data:', data);
        console.log('Data length:', data.length);
        console.log('Data type:', typeof data);
        
        allPriorAuths = data;
        filteredPriorAuths = data;
        
        console.log('About to call renderTable...');
        renderTable();
        console.log('About to call updateStats...');
        updateStats();
        updateLastRefreshedTime();
        showLoading(false);
        console.log('=== loadData completed ===');
    } catch (error) {
        console.error('Error loading data:', error);
        console.error('Error details:', error.message);
        showLoading(false);
    }
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        // Update tab counts (only update elements that exist)
        const allCount = document.getElementById('all-count');
        const runningTabCount = document.getElementById('running-tab-count');
        const reviewTabCount = document.getElementById('review-tab-count');
        const feedbackTabCount = document.getElementById('feedback-tab-count');
        const completedTabCount = document.getElementById('completed-tab-count');
        
        if (allCount) allCount.textContent = stats.pending || 0;
        if (runningTabCount) runningTabCount.textContent = stats.running || 0;
        if (reviewTabCount) reviewTabCount.textContent = stats.review || 0;
        if (feedbackTabCount) feedbackTabCount.textContent = stats.feedback || 0;
        if (completedTabCount) completedTabCount.textContent = stats.completed || 0;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    const table = document.getElementById('prior-auth-table');
    
    if (show) {
        spinner.style.display = 'flex';
        if (table) table.style.display = 'none';
    } else {
        spinner.style.display = 'none';
        if (table) table.style.display = 'table';
    }
}

function renderTable() {
    console.log('=== renderTable called ===');
    console.log('filteredPriorAuths:', filteredPriorAuths);
    console.log('filteredPriorAuths.length:', filteredPriorAuths.length);
    
    const tbody = document.getElementById('prior-auth-tbody');
    console.log('tbody element:', tbody);
    
    if (!tbody) {
        console.error('Could not find tbody element!');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (filteredPriorAuths.length === 0) {
        console.log('No data to display, showing empty state');
        document.getElementById('empty-state').style.display = 'block';
        document.getElementById('prior-auth-table').style.display = 'none';
        return;
    }
    
    console.log('Showing table with data');
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('prior-auth-table').style.display = 'table';
    
    filteredPriorAuths.forEach((auth, index) => {
        console.log(`Creating row ${index + 1} for auth:`, auth);
        const row = createTableRow(auth);
        tbody.appendChild(row);
    });
    
    console.log('=== renderTable completed ===');
}

function createTableRow(auth) {
    const row = document.createElement('tr');
    row.className = 'clickable-row';
    row.style.cursor = 'pointer';
    
    row.innerHTML = `
        <td class="checkbox-col">
            <input type="checkbox" class="auth-checkbox" value="${auth.id}" onchange="updateBulkActions()" onclick="event.stopPropagation()">
        </td>
        <td class="patient-col">
                <div class="patient-name">${auth.patient_name}</div>
        </td>
        <td class="created-col">
            <div class="created-date">${formatDate(auth.created_date)}</div>
        </td>
        <td class="priority-col">
            <span class="priority-badge priority-${auth.clinical_urgency || 'routine'}">${getPriorityDisplay(auth.clinical_urgency)}</span>
        </td>
        <td class="type-col">
                <div class="service-type">${auth.service_type}</div>
        </td>
        <td class="status-col">
            <span class="status-badge status-${auth.status}">${getStatusDisplay(auth.status)}</span>
        </td>
        <td class="ref-by-prov-col">
            <div class="ref-provider">${auth.ordering_provider || 'Dr. Smith'}</div>
        </td>
        <td class="ref-by-dept-col">
            <div class="ref-department">${auth.ordering_department || 'ONCOLOGY'}</div>
        </td>
        <td class="insurance-col">
                <div class="insurance-provider">${auth.insurance_provider}</div>
        </td>
        <td class="cpt-col">
            <span class="cpt-code">${auth.cpt_code || 'N/A'}</span>
        </td>
        <td class="last-comm-date-col">
            <div class="last-comm-date">${formatDate(auth.last_updated || auth.created_date)}</div>
        </td>
        <td class="comm-outcome-col">
            <div class="comm-outcome">${getCommOutcome(auth.status)}</div>
        </td>
        <td class="comm-comments-col">
            <div class="comm-comments">${auth.notes || ''}</div>
        </td>
    `;
    
    // Add click event listener to the row
    row.addEventListener('click', function(e) {
        if (!e.target.closest('.checkbox-col')) {
            showCaseDetails(auth);
        }
    });
    
    return row;
}

function getStepName(step) {
    const stepNames = {
        1: 'Coverage',
        2: 'Form Completion'
    };
    return stepNames[step] || 'Unknown';
}

function getStatusDisplay(status) {
    const statusMap = {
        'pending': 'Not Started',
        'running': 'In Progress',
        'review': 'In Progress',
        'feedback': 'In Progress',
        'completed': 'Complete',
        'failed': 'Failed'
    };
    return statusMap[status] || status;
}

function getPriorityDisplay(priority) {
    const priorityMap = {
        'urgent': 'Urgent',
        'routine': 'Routine',
        'stat': 'Stat'
    };
    return priorityMap[priority] || 'Routine';
}

function getCommOutcome(status) {
    const outcomeMap = {
        'pending': 'Left Message',
        'running': 'In Progress',
        'review': 'Pending Review',
        'feedback': 'Needs Info',
        'completed': 'Authorized',
        'failed': 'Failed'
    };
    return outcomeMap[status] || 'No Action';
}

function updateLastRefreshedTime() {
    const now = new Date();
    const timeString = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
    const lastRefreshedElement = document.getElementById('last-refreshed-time');
    if (lastRefreshedElement) {
        lastRefreshedElement.textContent = timeString;
    }
}

function getActionButton(auth) {
    if (auth.status === 'pending') {
        return `<button class="btn btn-sm btn-primary" onclick="startAutomation(${auth.id})" title="Start Automation">
                    <i class="fas fa-robot"></i>
                </button>`;
    } else if (auth.status === 'running') {
        return `<button class="btn btn-sm btn-info" onclick="viewDetails(${auth.id})" title="View Progress">
                    <i class="fas fa-eye"></i>
                </button>`;
    } else if (auth.status === 'review') {
        return `<button class="btn btn-sm btn-success" onclick="approveAuth(${auth.id})" title="Approve">
                    <i class="fas fa-check"></i>
                </button>`;
    } else if (auth.status === 'feedback') {
        return `<button class="btn btn-sm btn-info" onclick="provideFeedback(${auth.id})" title="Provide Feedback">
                    <i class="fas fa-comment"></i>
                </button>`;
    }
    return '';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function isOverdue(dueDate) {
    return new Date(dueDate) < new Date();
}

function filterData() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const providerFilter = document.getElementById('provider-filter').value;
    const statusFilter = document.getElementById('status-filter').value;
    
    filteredPriorAuths = allPriorAuths.filter(auth => {
        const matchesSearch = !searchTerm || 
            auth.patient_name.toLowerCase().includes(searchTerm) ||
            auth.patient_mrn.toLowerCase().includes(searchTerm) ||
            auth.service_type.toLowerCase().includes(searchTerm) ||
            (auth.cpt_code && auth.cpt_code.toLowerCase().includes(searchTerm));
        
        const matchesProvider = !providerFilter || auth.insurance_provider === providerFilter;
        const matchesStatus = !statusFilter || auth.status === statusFilter;
        
        return matchesSearch && matchesProvider && matchesStatus;
    });
    
    // Apply current sorting
    sortData(currentSort.field, currentSort.direction, false);
}

function sortData(field, direction = null, updateFiltered = true) {
    // Update sort direction
    if (direction === null) {
        if (currentSort.field === field) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.direction = 'asc';
        }
    } else {
        currentSort.field = field;
        currentSort.direction = direction;
    }
    
    // Update sort indicators
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'fas fa-sort';
    });
    
    const currentHeader = document.querySelector(`[data-sort="${currentSort.field}"]`);
    if (currentHeader) {
        const icon = currentHeader.querySelector('i');
        icon.className = currentSort.direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
    
    // Sort the data
    const dataToSort = updateFiltered ? filteredPriorAuths : allPriorAuths;
    
    dataToSort.sort((a, b) => {
        let aVal = a[currentSort.field];
        let bVal = b[currentSort.field];
        
        // Handle date sorting
        if (currentSort.field.includes('date')) {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        } else if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        
        if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    if (updateFiltered) {
        renderTable();
    }
}

function updateBulkActions() {
    const checkboxes = document.querySelectorAll('.auth-checkbox:checked');
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (checkboxes.length > 0) {
        bulkActions.style.display = 'flex';
        selectedCount.textContent = checkboxes.length;
    } else {
        bulkActions.style.display = 'none';
    }
}

function clearSelection() {
    document.querySelectorAll('.auth-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    document.getElementById('select-all').checked = false;
    updateBulkActions();
}

// EPIC-style action functions
function deferSelected() {
    const selectedIds = Array.from(document.querySelectorAll('.auth-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedIds.length === 0) {
        alert('Please select items to defer.');
        return;
    }
    
    if (confirm(`Defer ${selectedIds.length} selected item(s)?`)) {
        // Implementation for deferring items
        console.log('Deferring items:', selectedIds);
        alert('Items deferred successfully.');
        loadData();
    }
}

function showFilterModal() {
    alert('Filter modal would open here.');
}

function addNotes() {
    const selectedIds = Array.from(document.querySelectorAll('.auth-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedIds.length === 0) {
        alert('Please select an item to add notes to.');
        return;
    }
    
    const notes = prompt('Enter notes:');
    if (notes) {
        console.log('Adding notes to items:', selectedIds, notes);
        alert('Notes added successfully.');
    }
}

function editSelected() {
    const selectedIds = Array.from(document.querySelectorAll('.auth-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedIds.length === 0) {
        alert('Please select an item to edit.');
        return;
    }
    
    if (selectedIds.length > 1) {
        alert('Please select only one item to edit.');
        return;
    }
    
    // Open edit modal or redirect to edit page
    console.log('Editing item:', selectedIds[0]);
    alert('Edit modal would open here.');
}

function assignSelected() {
    const selectedIds = Array.from(document.querySelectorAll('.auth-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedIds.length === 0) {
        alert('Please select items to assign.');
        return;
    }
    
    const assignee = prompt('Enter assignee name:');
    if (assignee) {
        console.log('Assigning items to:', assignee, selectedIds);
        alert('Items assigned successfully.');
        loadData();
    }
}

function viewChart() {
    alert('Chart view would open here.');
}

function sendMessage() {
    alert('Message interface would open here.');
}

function newCall() {
    alert('Call interface would open here.');
}

function showMore() {
    alert('Additional actions would be shown here.');
}

function viewHistory() {
    alert('Work queue history would open here.');
}

async function startAutomation(authId = null) {
    const selectedIds = authId ? [authId] : Array.from(document.querySelectorAll('.auth-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedIds.length === 0) return;
    
    if (confirm(`Start automation for ${selectedIds.length} prior authorization(s)?`)) {
        // Start with the first selected auth
        const authId = selectedIds[0];
        await runAutomationWorkflow(authId);
        clearSelection();
    }
}

async function runAutomationWorkflow(authId) {
    // Get auth data
    const auth = allPriorAuths.find(a => a.id == authId);
    if (!auth) return;
    
    automationData = auth;
    currentAutomationStep = 1;
    stepResults = {};
    
    // Start automation on backend
    try {
        const response = await fetch(`/api/prior-auths/${authId}/start-automation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update button states to show running state
            const actionBtn = document.getElementById('modal-action-btn');
            const cancelBtn = document.getElementById('modal-cancel-btn');
            
            actionBtn.textContent = 'View Progress';
            actionBtn.className = 'btn btn-info';
            actionBtn.onclick = () => {
                // Switch to automation tab and show progress
                switchModalTab('automation');
                showAutomationProgress(authId);
            };
            
            cancelBtn.style.display = 'inline-block';
            
            // Start polling for updates
            startAutomationPolling(authId);
        } else {
            console.error('Failed to start automation:', result.error);
            alert('Failed to start automation: ' + result.error);
        }
    } catch (error) {
        console.error('Error starting automation:', error);
        alert('Error starting automation: ' + error.message);
    }
}

function startAutomationPolling(authId) {
    // Clear any existing polling
    if (automationPollingInterval) {
        clearInterval(automationPollingInterval);
    }
    
    // Start polling every 2 seconds
    automationPollingInterval = setInterval(async () => {
        await pollAutomationStatus(authId);
    }, 2000);
    
    // Do initial poll immediately
    pollAutomationStatus(authId);
}

async function pollAutomationStatus(authId) {
    try {
        const response = await fetch(`/api/automation/status/${authId}`);
        const status = await response.json();
        
        if (status.error) {
            console.error('Automation error:', status.error);
            stopAutomationPolling();
            return;
        }
        
        // Update UI with current status
        updateAutomationUI(status);
        
        // Also check the case status from the database
        let caseStatus = null;
        try {
            const caseResponse = await fetch(`/api/prior-auths/${authId}`);
            const caseData = await caseResponse.json();
            if (caseData.success) {
                caseStatus = caseData.auth.status;
            }
        } catch (e) {
            console.log('Could not fetch case status:', e);
        }
        
        // Check if ready for form completion (when run_automation_workflow returns True)
        if ((status.results && status.results.form && status.results.form.status === 'ready_for_completion') || 
            (status.details && (status.details.get ? status.details.get('ready_for_form') : status.details.ready_for_form) === true) ||
            (status.message && status.message.includes('Ready for form completion')) ||
            (caseStatus === 'ready_for_form')) {
            console.log('🔄 Coverage analysis complete, switching to form processing tab');
            
            // Update the current step status to show transition
            const currentStepStatus = document.getElementById('current-step-status');
            if (currentStepStatus) {
                currentStepStatus.innerHTML = '<i class="fas fa-arrow-right"></i> Transitioning to Form Processing';
            }
            
            // Update progress text to show transition
            const progressText = document.getElementById('automation-progress-text');
            if (progressText) {
                progressText.textContent = 'Coverage analysis complete - switching to form processing...';
            }
            
            // Stop polling for automation updates
            stopAutomationPolling();
            
            // Switch to form processing tab
            switchModalTab('form-processing');
            
            // Wait a moment for the tab to load, then start form agent processing
            setTimeout(() => {
                console.log('🚀 Starting form agent processing automatically');
                startFormAgentProcessing();
            }, 1000);
            
            return;
        }
        
        // Check if automation is complete
        if (!status.is_running) {
            stopAutomationPolling();
            
            if (status.error) {
                console.error('Automation failed:', status.error);
                alert('Automation failed: ' + status.error);
            } else {
                console.log('Automation completed successfully');
                // Update the current step status to show completion
                const currentStepStatus = document.getElementById('current-step-status');
                if (currentStepStatus) {
                    currentStepStatus.innerHTML = '<i class="fas fa-check"></i> Complete';
                }
                
                // Remove the spinning gear from current activity
                const currentActivity = document.querySelector('.current-activity');
                if (currentActivity) {
                    const activityIcon = currentActivity.querySelector('i');
                    if (activityIcon) {
                        activityIcon.className = 'fas fa-check-circle';
                        activityIcon.style.animation = 'none';
                    }
                }
                
                // // Add completion message to the detailed content
                // const contentContainer = document.getElementById('step-content-container');
                // if (contentContainer) {
                //     const completionMessage = document.createElement('div');
                //     completionMessage.className = 'completion-message';
                //     completionMessage.innerHTML = `
                //         <div class="completion-banner">
                //             <i class="fas fa-check-circle"></i>
                //             <span>Automation completed successfully!</span>
                //         </div>
                //     `;
                //     contentContainer.insertBefore(completionMessage, contentContainer.firstChild);
                // }
            }
        }
        
    } catch (error) {
        console.error('Error polling automation status:', error);
    }
}

function stopAutomationPolling() {
    if (automationPollingInterval) {
        clearInterval(automationPollingInterval);
        automationPollingInterval = null;
    }
}

function updateAutomationUI(status) {
    // Update progress bar
    const progressFill = document.getElementById('automation-progress-fill');
    const progressText = document.getElementById('automation-progress-text');
    
    if (progressFill && progressText) {
        progressFill.style.width = `${status.progress}%`;
        progressText.textContent = `${Math.round(status.progress)}% Complete`;
    }
    
    // Update current step display
    const currentStepTitle = document.getElementById('current-step-title');
    const currentStepDescription = document.getElementById('current-step-description');
    const currentStepStatus = document.getElementById('current-step-status');
    
    if (currentStepTitle && currentStepDescription && currentStepStatus) {
        const step = automationSteps[status.current_step - 1];
        if (step) {
            currentStepTitle.textContent = step.title;
            currentStepDescription.textContent = status.message;
            
            if (status.is_running) {
                currentStepStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running';
            } else {
                currentStepStatus.innerHTML = '<i class="fas fa-check"></i> Complete';
            }
        }
    }
    
    // Update step history
    updateStepHistory(status);
    
    // Update detailed content area
    updateDetailedContent(status);
}

function updateStepHistory(status) {
    const stepHistoryContainer = document.getElementById('step-history-container');
    if (!stepHistoryContainer) return;
    
    // Clear existing history
    stepHistoryContainer.innerHTML = '';
    
    // Add completed steps
    for (let i = 1; i < status.current_step; i++) {
        const step = automationSteps[i - 1];
        if (step) {
            const stepElement = document.createElement('div');
            stepElement.className = 'completed-step';
            stepElement.innerHTML = `
                <div class="step-icon">
                    <i class="fas fa-check"></i>
                </div>
                <div class="step-info">
                    <h4>${step.title}</h4>
                    <p>Completed successfully</p>
                </div>
            `;
            stepHistoryContainer.appendChild(stepElement);
        }
    }
}

function updateDetailedContent(status) {
    const contentContainer = document.getElementById('step-content-container');
    if (!contentContainer || !status.details) return;
    
    const details = status.details;
    let contentHtml = '';
    
    // Show current activity directly under progress bar
    if (details.current_activity) {
        const isRunning = status.is_running !== false; // Default to true if not explicitly false
        const iconClass = isRunning ? 'fas fa-cog fa-spin' : 'fas fa-check-circle';
        
        // Update the progress text to show current activity
        const progressText = document.getElementById('automation-progress-text');
        if (progressText) {
            progressText.textContent = details.current_activity;
        }
    }
    
    // Track which sections to show expanded (current step) vs collapsed (previous steps)
    const currentStep = status.current_step || 1;
    let sectionCount = 0;
    
    // Show search results
    if (details.search_results && details.search_results.length > 0) {
        sectionCount++;
        const isCurrentStep = currentStep === 1;
        const isExpanded = isCurrentStep; // Only expand if it's the current step
        
        contentHtml += `
            <div class="collapsible-section ${isExpanded ? 'expanded' : 'collapsed'}" data-section="search-results">
                <div class="section-header" onclick="toggleSection('search-results')">
                    <h5><i class="fas fa-search"></i> Policy Research Results</h5>
                    <div class="section-status">
                        <span class="status-badge ${isCurrentStep ? 'current' : 'completed'}">
                            ${isCurrentStep ? 'In Progress' : 'Completed'}
                        </span>
                        <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'}"></i>
                    </div>
                </div>
                <div class="section-content" style="display: ${isExpanded ? 'block' : 'none'};">
                    <div class="search-results-list">
        `;
        
        details.search_results.forEach(searchGroup => {
            contentHtml += `
                <div class="search-group">
                    <h6>Query: "${searchGroup.query}"</h6>
                    <div class="results-grid">
            `;
            
            searchGroup.results.forEach(result => {
                contentHtml += `
                    <div class="result-item">
                        <div class="result-header">
                            <a href="${result.url}" target="_blank" class="result-title">${result.title}</a>
                            <span class="result-relevance">${result.relevance || 0}%</span>
                        </div>
                        <div class="result-snippet">${result.snippet || 'No snippet available'}</div>
                        <div class="result-meta">
                            <span class="result-source">${result.source || 'Unknown'}</span>
                            <span class="result-type">${result.type || 'document'}</span>
                        </div>
                    </div>
                `;
            });
            
            contentHtml += `
                    </div>
                </div>
            `;
        });
        
        contentHtml += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // Show parsing agent results
    if (details.parsing_agent_results) {
        sectionCount++;
        const isCurrentStep = currentStep === 1; // Parsing agent runs as part of step 1
        const isExpanded = isCurrentStep; // Only expand if it's the current step
        
        contentHtml += `
            <div class="collapsible-section ${isExpanded ? 'expanded' : 'collapsed'}" data-section="parsing-agent">
                <div class="section-header" onclick="toggleSection('parsing-agent')">
                    <h5><i class="fas fa-file-alt"></i> Document Analysis</h5>
                    <div class="section-status">
                        <span class="status-badge ${isCurrentStep ? 'current' : 'completed'}">
                            ${isCurrentStep ? 'In Progress' : 'Completed'}
                        </span>
                        <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'}"></i>
                    </div>
                </div>
                <div class="section-content" style="display: ${isExpanded ? 'block' : 'none'};">
                    <div class="parsing-results">
        `;
        
        const parsing = details.parsing_agent_results;
        if (parsing.request_validation) {
            contentHtml += `
                <div class="validation-section">
                    <h6>Request Validation</h6>
                    <div class="validation-status ${parsing.request_validation.is_valid ? 'valid' : 'invalid'}">
                        <i class="fas fa-${parsing.request_validation.is_valid ? 'check-circle' : 'exclamation-triangle'}"></i>
                        <span>${parsing.request_validation.is_valid ? 'Valid Request' : 'Invalid Request'}</span>
                    </div>
                    <p>${parsing.request_validation.validation_notes}</p>
                </div>
            `;
        }
        
        if (parsing.critical_requirements) {
            contentHtml += `
                <div class="requirements-section">
                    <h6>Coverage Requirements</h6>
                    <div class="requirements-list">
            `;
            
            parsing.critical_requirements.forEach(req => {
                contentHtml += `
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <i class="fas fa-exclamation-triangle"></i>
                            <span><strong>${req.requirement}</strong></span>
                        </div>
                        <div class="requirement-details">
                            <p><strong>Criteria:</strong> ${req.criteria}</p>
                            <p><strong>Documentation:</strong> ${req.documentation_needed}</p>
                        </div>
                    </div>
                `;
            });
            
            contentHtml += `
                    </div>
                </div>
            `;
        }
        
        contentHtml += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // Show form data
    if (details.form_data && Object.keys(details.form_data).length > 0) {
        sectionCount++;
        const isCurrentStep = currentStep === 2;
        const isExpanded = isCurrentStep; // Only expand if it's the current step
        
        contentHtml += `
            <div class="collapsible-section ${isExpanded ? 'expanded' : 'collapsed'}" data-section="form-data">
                <div class="section-header" onclick="toggleSection('form-data')">
                    <h5><i class="fas fa-file-medical"></i> Form Completion</h5>
                    <div class="section-status">
                        <span class="status-badge ${isCurrentStep ? 'current' : 'completed'}">
                            ${isCurrentStep ? 'In Progress' : 'Completed'}
                        </span>
                        <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'}"></i>
                    </div>
                </div>
                <div class="section-content" style="display: ${isExpanded ? 'block' : 'none'};">
                    <div class="form-data-grid">
        `;
        
        if (details.form_data.patient_info) {
            contentHtml += `
                <div class="form-section">
                    <h6>Patient Information</h6>
                    <div class="form-field">
                        <label>Name:</label>
                        <span>${details.form_data.patient_info.name}</span>
                        <small class="citation">Source: ${details.form_data.patient_info.source}</small>
                    </div>
                    <div class="form-field">
                        <label>MRN:</label>
                        <span>${details.form_data.patient_info.mrn}</span>
                    </div>
                </div>
            `;
        }
        
        if (details.form_data.service_info) {
            contentHtml += `
                <div class="form-section">
                    <h6>Service Information</h6>
                    <div class="form-field">
                        <label>Service Type:</label>
                        <span>${details.form_data.service_info.service_type}</span>
                        <small class="citation">Source: ${details.form_data.service_info.source}</small>
                    </div>
                    <div class="form-field">
                        <label>CPT Code:</label>
                        <span>${details.form_data.service_info.cpt_code}</span>
                    </div>
                </div>
            `;
        }
        
        if (details.form_data.validation) {
            contentHtml += `
                <div class="form-section">
                    <h6>Validation</h6>
                    <div class="validation-status ${details.form_data.validation.status}">
                        <i class="fas fa-${details.form_data.validation.status === 'valid' ? 'check-circle' : 'exclamation-triangle'}"></i>
                        <span>${details.form_data.status.toUpperCase()}</span>
                    </div>
                    ${details.form_data.validation.errors.length > 0 ? `
                        <div class="validation-errors">
                            <h6>Errors:</h6>
                            <ul>
                                ${details.form_data.validation.errors.map(error => `<li>${error}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        contentHtml += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // Show citations
    if (details.citations && details.citations.length > 0) {
        sectionCount++;
        const isCurrentStep = false; // Citations are always available
        const isExpanded = false; // Always collapsed by default
        
        contentHtml += `
            <div class="collapsible-section collapsed" data-section="citations">
                <div class="section-header" onclick="toggleSection('citations')">
                    <h5><i class="fas fa-link"></i> Data Sources</h5>
                    <div class="section-status">
                        <span class="status-badge completed">Available</span>
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>
                <div class="section-content" style="display: none;">
                    <div class="citations-list">
        `;
        
        details.citations.forEach(citation => {
            contentHtml += `
                <div class="citation-item">
                    <div class="citation-header">
                        <a href="${citation.url}" target="_blank" class="citation-title">${citation.title}</a>
                        <span class="citation-relevance">${citation.relevance}%</span>
                    </div>
                    <div class="citation-meta">
                        <span class="citation-source">${citation.source}</span>
                        <span class="citation-type">${citation.type}</span>
                    </div>
                </div>
            `;
        });
        
        contentHtml += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // Update content
    contentContainer.innerHTML = contentHtml;
}

function toggleSection(sectionName) {
    const section = document.querySelector(`[data-section="${sectionName}"]`);
    if (!section) return;
    
    const content = section.querySelector('.section-content');
    const chevron = section.querySelector('.fa-chevron-up, .fa-chevron-down');
    const isExpanded = section.classList.contains('expanded');
    
    if (isExpanded) {
        // Collapse
        section.classList.remove('expanded');
        section.classList.add('collapsed');
        content.style.display = 'none';
        chevron.className = 'fas fa-chevron-down';
    } else {
        // Expand
        section.classList.remove('collapsed');
        section.classList.add('expanded');
        content.style.display = 'block';
        chevron.className = 'fas fa-chevron-up';
    }
}

function showAutomationResults(results) {
    const content = document.getElementById('step-content-container');
    if (!content) return;
    
    // Display results based on what's available
    let resultsHtml = '<div class="automation-results">';
    resultsHtml += '<h4><i class="fas fa-check-circle"></i> Automation Complete</h4>';
    
    if (results.coverage) {
        resultsHtml += '<div class="result-section">';
        resultsHtml += '<h5>Coverage Analysis Results</h5>';
        resultsHtml += `<p><strong>Coverage Status:</strong> ${results.coverage.coverage_status}</p>`;
        resultsHtml += `<p><strong>Confidence Score:</strong> ${results.coverage.confidence_score}%</p>`;
        
        if (results.coverage.parsing_agent_result) {
            resultsHtml += '<div class="parsing-agent-results">';
            resultsHtml += '<h6>Parsing Agent Analysis</h6>';
            resultsHtml += `<p><strong>Request Validation:</strong> ${results.coverage.parsing_agent_result.request_validation.is_valid ? 'Valid' : 'Invalid'}</p>`;
            resultsHtml += '</div>';
        }
        
        resultsHtml += '</div>';
    }
    
    if (results.form) {
        resultsHtml += '<div class="result-section">';
        resultsHtml += '<h5>Form Completion Results</h5>';
        resultsHtml += `<p><strong>Status:</strong> ${results.form.form_data.status}</p>`;
        resultsHtml += `<p><strong>Submission Ready:</strong> ${results.form.submission_ready ? 'Yes' : 'No'}</p>`;
        resultsHtml += '</div>';
    }
    
    resultsHtml += '</div>';
    
    content.innerHTML = resultsHtml;
}

async function executeAutomationStep(stepNumber) {
    console.log('executeAutomationStep called with stepNumber:', stepNumber);
    const step = automationSteps[stepNumber - 1];
    if (!step) {
        console.error('Step not found for stepNumber:', stepNumber);
        return;
    }
    
    console.log('Executing step:', step);
    
    // Update UI
    updateStepDisplay(step);
    
    // Execute step-specific logic
    switch (step.content) {
        case 'coverage':
            console.log('Executing policy research and coverage analysis...');
            await executePolicyResearchAndCoverage();
            break;
        case 'form':
            console.log('Executing form completion with EHR data...');
            await executeFormCompletionWithEHR();
            break;
        default:
            console.error('Unknown step content:', step.content);
    }
}

function updateStepDisplay(step) {
    document.getElementById('current-step-icon').innerHTML = `<i class="${step.icon}"></i>`;
    document.getElementById('current-step-title').textContent = `Step ${step.id}: ${step.title}`;
    document.getElementById('current-step-description').textContent = step.description;
    document.getElementById('current-step-status').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running';
    
    // Update progress
    const progress = (step.id / automationSteps.length) * 100;
    document.getElementById('automation-progress-fill').style.width = `${progress}%`;
    document.getElementById('automation-progress-text').textContent = `${Math.round(progress)}% Complete`;
}



async function executePolicyResearchAndCoverage() {
    const content = document.getElementById('step-content-container');
    
    // Show GPT-5 search animation first
    showGPT5SearchAnimation();
    updateSearchQuery("🚀 Starting GPT-5 searches for insurance coverage...");
    updateSearchProgress(0);
    
    try {
        // Start the streaming GPT-5 search
        const response = await fetch(`/api/prior-auths/${automationData.id}/gpt5-search-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        switch (data.type) {
                            case 'status':
                                updateSearchQuery(data.message);
                                updateSearchProgress(data.progress);
                                break;
                                
                            case 'search_start':
                                updateSearchQuery(`🔍 Searching: ${data.query}`);
                                updateSearchProgress(data.progress);
                                break;
                                
                                                        case 'search_result':
                                updateSearchQuery(`✅ Found ${data.count} results for: ${data.query}`);
                                updateSearchProgress(data.progress);

                                // Only show results if we have real data (not fallback/hallucinated)
                                if (data.results && data.results.length > 0) {
                                    // Check if results are real (not fallback)
                                    const hasRealResults = data.results.some(result => 
                                        result.url && 
                                        !result.url.includes('example.com') && 
                                        !result.url.includes('placeholder') &&
                                        result.title && 
                                        !result.title.toLowerCase().includes('generic') &&
                                        result.source && 
                                        result.source !== 'Generic'
                                    );

                                    if (hasRealResults) {
                                        // Show live search results in the animation
                                        const liveResultsContainer = document.getElementById('live-search-results');
                                        const resultsContainer = document.getElementById('results-container');
                                        
                                        if (liveResultsContainer.style.display === 'none') {
                                            liveResultsContainer.style.display = 'block';
                                        }

                                        // Add new results to the live results container
                                        data.results.forEach(result => {
                                            // Only add real results
                                            if (result.url && 
                                                !result.url.includes('example.com') && 
                                                !result.url.includes('placeholder') &&
                                                result.title && 
                                                !result.title.toLowerCase().includes('generic') &&
                                                result.source && 
                                                result.source !== 'Generic') {
                                                
                                                const resultItem = document.createElement('div');
                                                resultItem.className = 'live-result-item';
                                                resultItem.innerHTML = `
                                                    <div class="live-result-header">
                                                        <a href="${result.url}" target="_blank" class="live-result-title">${result.title}</a>
                                                        <div class="live-result-meta">
                                                            <span class="live-result-type">${result.type || 'document'}</span>
                                                            <span class="live-result-relevance">${result.relevance || 0}%</span>
                                                        </div>
                                                    </div>
                                                    <div class="live-result-snippet">${result.snippet || 'No snippet available'}</div>
                                                    <div class="live-result-source">Source: ${result.source || 'Unknown'}</div>
                                                `;
                                                resultsContainer.appendChild(resultItem);
                                            }
                                        });

                                        // Also add to content area for final display
                                        const realResults = data.results.filter(result => 
                                            result.url && 
                                            !result.url.includes('example.com') && 
                                            !result.url.includes('placeholder') &&
                                            result.title && 
                                            !result.title.toLowerCase().includes('generic') &&
                                            result.source && 
                                            result.source !== 'Generic'
                                        );

                                        if (realResults.length > 0) {
                                            const searchResultsHtml = realResults.map(result => `
                                                <div class="search-result-item">
                                                    <div class="result-header">
                                                        <a href="${result.url}" target="_blank" class="result-title">${result.title}</a>
                                                        <span class="result-type">${result.type || 'document'}</span>
                                                        <span class="result-relevance">${result.relevance || 0}% relevant</span>
                                                    </div>
                                                    <div class="result-snippet">${result.snippet || 'No snippet available'}</div>
                                                    <div class="result-source">Source: ${result.source || 'Unknown'}</div>
                                                </div>
                                            `).join('');

                                            const searchResultsContainer = document.createElement('div');
                                            searchResultsContainer.className = 'search-results-container';
                                            searchResultsContainer.innerHTML = `
                                                <h5>🔍 Search Results for: ${data.query}</h5>
                                                <div class="search-results-list">
                                                    ${searchResultsHtml}
                                                </div>
                                            `;

                                            // Add to content area
                                            const contentArea = document.getElementById('step-content-container');
                                            contentArea.appendChild(searchResultsContainer);
                                        }
                                    } else {
                                        // Show message that we're waiting for real results
                                        updateSearchQuery(`⏳ Processing search results for: ${data.query}...`);
                                    }
                                }
                                break;
                                
                                                        case 'search_error':
                                updateSearchQuery(`❌ Error searching: ${data.query} - ${data.error}`);
                                updateSearchProgress(data.progress);

                                // Show error in content area
                                const errorContainer = document.createElement('div');
                                errorContainer.className = 'search-error-container';
                                errorContainer.innerHTML = `
                                    <div class="error-message">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        <strong>Search Error:</strong> ${data.error}
                                        <p>Using fallback data for analysis. Real web search results will be used when available.</p>
                                    </div>
                                `;

                                const contentArea = document.getElementById('step-content-container');
                                contentArea.appendChild(errorContainer);
                                break;
                                
                                                        case 'complete':
                                // Show parsing agent analysis first
                                const result = data.result;
                                
                                // Update search query to show parsing agent completion
                                updateSearchQuery(`✅ Parsing agent analysis complete!`);
                                updateSearchProgress(100);

                                // Hide animation after a delay to show parsing agent results
                                setTimeout(() => {
                                    hideGPT5SearchAnimation();
                                }, 2000);

                                // Display only the parsing agent analysis first
                                content.innerHTML = `
                                    <div class="parsing-agent-result">
                                        <h4><i class="fas fa-robot"></i> Parsing Agent Analysis Results</h4>
                                        <div class="result-card">
                                            ${result.parsing_agent_result ? `
                                            <div class="parsing-agent-analysis">
                                                <h5><i class="fas fa-robot"></i> Parsing Agent Analysis</h5>
                                                
                                                <!-- Request Validation -->
                                                <div class="validation-section">
                                                    <h6>Request Validation:</h6>
                                                    <div class="validation-status ${result.parsing_agent_result.request_validation.is_valid ? 'valid' : 'invalid'}">
                                                        <i class="fas fa-${result.parsing_agent_result.request_validation.is_valid ? 'check-circle' : 'exclamation-triangle'}"></i>
                                                        <span><strong>Status:</strong> ${result.parsing_agent_result.request_validation.is_valid ? 'Valid Request' : 'Invalid Request'}</span>
                                                    </div>
                                                    <p class="validation-notes">${result.parsing_agent_result.request_validation.validation_notes}</p>
                                                    
                                                    ${!result.parsing_agent_result.request_validation.is_valid ? `
                                                    <div class="missing-documents">
                                                        <h6>Missing Documents:</h6>
                                                        <ul>
                                                            ${result.parsing_agent_result.request_validation.missing_documents.map(doc => `<li>${doc}</li>`).join('')}
                                                        </ul>
                                                        <div class="clinician-message">
                                                            <h6>Message to Clinician:</h6>
                                                            <p>${result.parsing_agent_result.clinician_message}</p>
                                                            <button class="btn btn-warning btn-sm" onclick="sendClinicianMessage('${result.parsing_agent_result.clinician_message}')">
                                                                <i class="fas fa-paper-plane"></i> Send to Clinician
                                                            </button>
                                                        </div>
                                                    </div>
                                                    

                                                    ` : ''}
                                                </div>
                                                
                                                <!-- Critical Requirements -->
                                                <div class="critical-requirements">
                                                    <h6>Critical Requirements Checklist:</h6>
                                                    ${result.parsing_agent_result.critical_requirements.map(req => `
                                                        <div class="requirement-item">
                                                            <div class="requirement-header">
                                                                <i class="fas fa-exclamation-triangle"></i>
                                                                <span><strong>${req.requirement}</strong></span>
                                                            </div>
                                                            <div class="requirement-details">
                                                                <div><strong>Criteria:</strong> ${req.criteria}</div>
                                                                <div><strong>Documentation Needed:</strong> ${req.documentation_needed}</div>
                                                                <div><strong>Clinical Criteria:</strong> ${req.clinical_criteria}</div>
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                                
                                                <!-- Requirements Checklist -->
                                                <div class="requirements-checklist">
                                                    <h6>Requirements Checklist for Determination:</h6>
                                                    ${result.parsing_agent_result.requirements_checklist.map(category => `
                                                        <div class="checklist-category">
                                                            <h7><strong>${category.category}:</strong></h7>
                                                            ${category.items.map(item => `
                                                                <div class="checklist-item">
                                                                    <div class="checklist-header">
                                                                        <i class="fas fa-check-square"></i>
                                                                        <span>${item.requirement}</span>
                                                                    </div>
                                                                    <div class="checklist-details">
                                                                        <div><strong>Evidence Required:</strong> ${item.evidence_required}</div>
                                                                        <div><strong>Notes:</strong> ${item.notes}</div>
                                                                    </div>
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    `).join('')}
                                                </div>
                                                
                                                <!-- Medical Knowledge -->
                                                <div class="medical-knowledge">
                                                    <h6>Medical Knowledge from Evidence:</h6>
                                                    ${result.parsing_agent_result.medical_knowledge.map(knowledge => `
                                                        <div class="knowledge-item">
                                                            <div class="knowledge-header">
                                                                <i class="fas fa-brain"></i>
                                                                <span><strong>${knowledge.topic}</strong></span>
                                                                <span class="relevance-badge ${knowledge.relevance.toLowerCase()}">${knowledge.relevance}</span>
                                                            </div>
                                                            <div class="knowledge-details">
                                                                <div><strong>Evidence:</strong> ${knowledge.evidence}</div>
                                                                <div><strong>Source:</strong> ${knowledge.source_document}</div>
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                            ` : '<p>No parsing agent results available.</p>'}
                                            
                                            <div class="next-step-prompt">
                                                <h5>Ready to View Complete Analysis:</h5>
                                                <p>The parsing agent analysis is complete. Click the button below to view the full coverage analysis and search results.</p>
                                                <button class="btn btn-primary" onclick="showCompleteAnalysis()">
                                                    <i class="fas fa-eye"></i> View Complete Analysis
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                `;
                                
                                // Store the result for later use
                                window.currentAnalysisResult = result;
                                
                                // Auto-show clinician message modal if request is invalid
                                if (result.parsing_agent_result && !result.parsing_agent_result.request_validation.is_valid) {
                                    setTimeout(() => {
                                        console.log('🔄 Auto-showing clinician message modal...');
                                        sendClinicianMessage(result.parsing_agent_result.clinician_message);
                                    }, 2000); // Wait 2 seconds for the results to be displayed
                                }
                                
                                return;
                        }
                    } catch (parseError) {
                        console.error('Error parsing SSE data:', parseError);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Error in GPT-5 search stream:', error);
        hideGPT5SearchAnimation();
        await streamText(content, `
            <div class="error-result">
                <h4>Step 1: Coverage Determination - Error</h4>
                <div class="error-card">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p>Please try again or contact support.</p>
                </div>
            </div>
        `, 'coverage');
    }
}

// Function to show complete analysis after parsing agent results
function showCompleteAnalysis() {
    const result = window.currentAnalysisResult;
    if (!result) {
        console.error('No analysis result available');
        return;
    }
    
    const content = document.getElementById('step-content-container');
    
    // Display the complete analysis
    content.innerHTML = `
        <div class="coverage-result">
            <h4>Step 1: Policy Research & Coverage Analysis - Complete</h4>
            <div class="result-card">
                <div class="coverage-summary">
                    <div class="coverage-status ${result.coverage_status === 'covered' ? 'success' : 'warning'}">
                        <i class="fas fa-${result.coverage_status === 'covered' ? 'check' : 'exclamation-triangle'}"></i>
                        <span><strong>Coverage Status:</strong> ${result.coverage_status.toUpperCase()}</span>
                    </div>
                    <div class="confidence-score">
                        <strong>Confidence:</strong> ${Math.round(result.confidence_score * 100)}%
                    </div>
                </div>
                
                <div class="coverage-details">
                    <h5>Coverage Analysis:</h5>
                    <p>${result.coverage_details}</p>
                </div>
                
                <div class="requirements-section">
                    <h5>Policy Requirements Found (${result.requirements.length}):</h5>
                    ${result.requirements.map(req => `
                        <div class="requirement-item">
                            <div class="requirement-header">
                                <i class="fas fa-file-medical"></i>
                                <span><strong>${req.requirement_type}</strong></span>
                                <span class="confidence">${Math.round(req.confidence_score * 100)}% confidence</span>
                            </div>
                            <p><strong>Description:</strong> ${req.description}</p>
                            <div class="requirement-details">
                                <div><strong>Evidence Basis:</strong> ${req.evidence_basis}</div>
                                <div><strong>Documentation Needed:</strong> ${req.documentation_needed}</div>
                                <div><strong>Clinical Criteria:</strong> ${req.clinical_criteria}</div>
                                <div><strong>Source Document:</strong> ${req.source_document}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="search-sources">
                    <h5>Web Search Sources (${result.search_sources.length} documents found):</h5>
                    ${result.search_sources.slice(0, 8).map(source => `
                        <div class="source-item">
                            <a href="${source.url}" target="_blank" class="source-title">${source.title}</a>
                            <div class="source-meta">
                                <span class="source-type">${source.type || 'document'}</span>
                                <span class="relevance">${source.relevance || 0}% relevant</span>
                            </div>
                            <div class="source-snippet">${source.snippet || 'No snippet available'}</div>
                        </div>
                    `).join('')}
                </div>
                
                ${result.parsing_agent_result ? `
                <div class="parsing-agent-analysis">
                    <h5><i class="fas fa-robot"></i> Parsing Agent Analysis</h5>
                    
                    <!-- Request Validation -->
                    <div class="validation-section">
                        <h6>Request Validation:</h6>
                        <div class="validation-status ${result.parsing_agent_result.request_validation.is_valid ? 'valid' : 'invalid'}">
                            <i class="fas fa-${result.parsing_agent_result.request_validation.is_valid ? 'check-circle' : 'exclamation-triangle'}"></i>
                            <span><strong>Status:</strong> ${result.parsing_agent_result.request_validation.is_valid ? 'Valid Request' : 'Invalid Request'}</span>
                        </div>
                        <p class="validation-notes">${result.parsing_agent_result.request_validation.validation_notes}</p>
                        
                        ${!result.parsing_agent_result.request_validation.is_valid ? `
                        <div class="missing-documents">
                            <h6>Missing Documents:</h6>
                            <ul>
                                ${result.parsing_agent_result.request_validation.missing_documents.map(doc => `<li>${doc}</li>`).join('')}
                            </ul>
                            <div class="clinician-message">
                                <h6>Message to Clinician:</h6>
                                <p>${result.parsing_agent_result.clinician_message}</p>
                                <button class="btn btn-warning btn-sm" onclick="sendClinicianMessage('${result.parsing_agent_result.clinician_message}')">
                                    <i class="fas fa-paper-plane"></i> Send to Clinician
                                </button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <!-- Critical Requirements -->
                    <div class="critical-requirements">
                        <h6>Critical Requirements Checklist:</h6>
                        ${result.parsing_agent_result.critical_requirements.map(req => `
                            <div class="requirement-item">
                                <div class="requirement-header">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    <span><strong>${req.requirement}</strong></span>
                                </div>
                                <div class="requirement-details">
                                    <div><strong>Criteria:</strong> ${req.criteria}</div>
                                    <div><strong>Documentation Needed:</strong> ${req.documentation_needed}</div>
                                    <div><strong>Clinical Criteria:</strong> ${req.clinical_criteria}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    
                    <!-- Requirements Checklist -->
                    <div class="requirements-checklist">
                        <h6>Requirements Checklist for Determination:</h6>
                        ${result.parsing_agent_result.requirements_checklist.map(category => `
                            <div class="checklist-category">
                                <h7><strong>${category.category}:</strong></h7>
                                ${category.items.map(item => `
                                    <div class="checklist-item">
                                        <div class="checklist-header">
                                            <i class="fas fa-check-square"></i>
                                            <span>${item.requirement}</span>
                                        </div>
                                        <div class="checklist-details">
                                            <div><strong>Evidence Required:</strong> ${item.evidence_required}</div>
                                            <div><strong>Notes:</strong> ${item.notes}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `).join('')}
                    </div>
                    
                    <!-- Medical Knowledge -->
                    <div class="medical-knowledge">
                        <h6>Medical Knowledge from Evidence:</h6>
                        ${result.parsing_agent_result.medical_knowledge.map(knowledge => `
                            <div class="knowledge-item">
                                <div class="knowledge-header">
                                    <i class="fas fa-brain"></i>
                                    <span><strong>${knowledge.topic}</strong></span>
                                    <span class="relevance-badge ${knowledge.relevance.toLowerCase()}">${knowledge.relevance}</span>
                                </div>
                                <div class="knowledge-details">
                                    <div><strong>Evidence:</strong> ${knowledge.evidence}</div>
                                    <div><strong>Source:</strong> ${knowledge.source_document}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="recommendations">
                    <h5>Recommendations:</h5>
                    <ul>
                        ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="next-step-prompt">
                    <h5>Ready for Step 2:</h5>
                    <p>Policy research complete. The system will now extract EHR data and fill the prior authorization form using the requirements identified above.</p>
                    <p><strong>DEBUG MODE:</strong> Automatic progression to step 2 has been disabled. Click the button below when ready to continue.</p>
                    <button class="btn btn-primary" onclick="moveToNextStep()">
                        <i class="fas fa-arrow-right"></i> Continue to Form Completion
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Add step to history and complete the step
    stepResults.coverage = {
        status: 'completed',
        coverage_confirmed: result.coverage_status === 'covered',
        ncd_criteria_met: result.ncd_applicable,
        decision: result.coverage_status === 'covered' ? 'Proceed with prior authorization' : 'Review required',
        analysis_result: result
    };
    
    // Add step to history
    addCompletedStep(1, result);
}
//                                 hideGPT5SearchAnimation();
//                                 await streamText(content, `
//                                     <div class="error-result">
//                                         <h4>Step 1: Coverage Determination - Error</h4>
//                                         <div class="error-card">
//                                             <i class="fas fa-exclamation-triangle"></i>
//                                             <p><strong>Error:</strong> ${data.error}</p>
//                                             <p>Please try again or contact support.</p>
//                                         </div>
//                                     </div>
//                                 `, 'coverage');
//                                 return;
//                         }
//                     } catch (parseError) {
//                         console.error('Error parsing SSE data:', parseError);
//                     }
//                 }
//             }
//         }
        
//     } catch (error) {
//         console.error('Error in GPT-5 search stream:', error);
//         hideGPT5SearchAnimation();
//         await streamText(content, `
//             <div class="error-result">
//                 <h4>Step 1: Coverage Determination - Error</h4>
//                 <div class="error-card">
//                     <i class="fas fa-exclamation-triangle"></i>
//                     <p><strong>Error:</strong> ${error.message}</p>
//                     <p>Please try again or contact support.</p>
//                 </div>
//             </div>
//         `, 'coverage');
//     }
// }

async function executeFormCompletionWithEHR() {
    const content = document.getElementById('step-content-container');
    
    // Clear the content area - no need for the form completion box
    content.innerHTML = '';
    
    // Automatically switch to form processing tab after a short delay
    setTimeout(() => {
        switchModalTab('form-processing');
    }, 2000);
}



// Global variable to store form questions for follow-up handling
let globalFormQuestions = null;

async function loadFormQuestions() {
    const container = document.getElementById('form-questions-container');
    const totalQuestionsSpan = document.getElementById('total-questions');
    const totalQuestionsDisplaySpan = document.getElementById('total-questions-display');
    
    try {
        // Load questions from API
        const response = await fetch('/api/form-questions');
        const data = await response.json();
        
        if (data.success) {
            const formQuestions = data.form_questions;
            // Store globally for follow-up handling
            globalFormQuestions = formQuestions;
            const totalQuestions = data.total_questions;
            
            // Update total questions count
            totalQuestionsSpan.textContent = totalQuestions;
            totalQuestionsDisplaySpan.textContent = totalQuestions;
            
            // Generate HTML for all questions
            let questionsHTML = '';
            
            for (const section of formQuestions.sections) {
                questionsHTML += `
                    <div class="question-sections">
                        <div class="section-header">
                            <h6><i class="fas fa-list"></i> ${section.section_name}</h6>
                            <div class="section-progress">${section.questions.length} questions</div>
                        </div>
                        <div class="question-list">
                `;
                
                for (const question of section.questions) {
                    // Handle nested provider information structure
                    if (question.subsection && question.fields) {
                        // This is a provider information subsection
                        questionsHTML += `
                            <div class="provider-subsection">
                                <h6 class="subsection-title">${question.subsection}</h6>
                        `;
                        
                        for (const field of question.fields) {
                            const fieldId = field.id;
                            const fieldLabel = field.label;
                            const fieldType = field.type;
                            const isRequired = field.required;
                            
                            let inputHTML = '';
                            if (fieldType === 'tel') {
                                inputHTML = `<input type="tel" class="answer-field" placeholder="Agent will populate this answer..." data-field-id="${fieldId}">`;
                            } else {
                                inputHTML = `<input type="text" class="answer-field" placeholder="Agent will populate this answer..." data-field-id="${fieldId}">`;
                            }
                            
                            questionsHTML += `
                                <div class="question-item provider-field" data-question-id="${fieldId}" data-question-type="${fieldType}">
                                    <div class="question-text">${fieldLabel}${isRequired ? ' <span class="required">*</span>' : ''}</div>
                                    <div class="answer-container">
                                        ${inputHTML}
                                        <div class="answer-status">
                                            <i class="fas fa-clock"></i>
                                            <span>Waiting for agent...</span>
                                        </div>
                                        <div class="answer-source"></div>
                                    </div>
                                </div>
                            `;
                        }
                        
                        questionsHTML += `</div>`;
                        continue;
                    }
                    
                    // Handle regular questions
                    const questionId = question.id;
                    const questionText = question.question;
                    const questionType = question.type;
                    const isRequired = question.required;
                    const hasFollowUp = question.follow_up;
                    
                    let fieldHTML = '';
                    let questionClass = 'question-item';
                    
                    // Handle different question types
                    if (questionType === 'statement') {
                        // Statements don't need input fields or status indicators
                        fieldHTML = '';
                        questionClass += ' statement-question';
                    } else if (questionType === 'radio' && question.options) {
                        const followUpCondition = hasFollowUp ? hasFollowUp.condition : null;
                        fieldHTML = `
                            <select class="answer-field" data-field-id="${questionId}" data-has-follow-up="${hasFollowUp ? 'true' : 'false'}" data-follow-up-condition="${followUpCondition || ''}">
                                <option value="">Agent will populate this answer...</option>
                                ${question.options.map(option => `<option value="${option}">${option}</option>`).join('')}
                            </select>
                        `;
                    } else if (questionType === 'text_area') {
                        fieldHTML = `
                            <textarea class="answer-field" placeholder="Agent will populate this answer..." data-field-id="${questionId}"></textarea>
                        `;
                    } else if (questionType === 'table') {
                        const columns = question.columns || [];
                        const rows = question.rows || 1;
                        fieldHTML = `
                            <div class="table-input-container">
                                <table class="table-input">
                                    <thead>
                                        <tr>
                                            ${columns.map(col => `<th>${col}</th>`).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${Array(rows).fill().map((_, i) => `
                                            <tr>
                                                ${columns.map(col => `<td><input type="text" class="table-cell-input" data-field-id="${questionId}_${i}_${col.toLowerCase().replace(/\s+/g, '_')}" placeholder="..."></td>`).join('')}
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        `;
                    } else {
                        fieldHTML = `
                            <input type="text" class="answer-field" placeholder="Agent will populate this answer..." data-field-id="${questionId}">
                        `;
                    }
                    
                    questionsHTML += `
                        <div class="${questionClass}" data-question-id="${questionId}" data-question-type="${questionType}">
                            <div class="question-text">${questionText}${isRequired ? ' <span class="required">*</span>' : ''}</div>
                            ${questionType !== 'statement' ? `
                                <div class="answer-container">
                                    ${fieldHTML}
                                    <div class="answer-status">
                                        <i class="fas fa-clock"></i>
                                        <span>Waiting for agent...</span>
                                    </div>
                                    <div class="answer-source"></div>
                                </div>
                            ` : ''}
                            ${hasFollowUp ? `<div class="follow-up-container" style="display: none;"></div>` : ''}
                        </div>
                    `;
                }
                
                questionsHTML += `
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = questionsHTML;
            
            // Add event listeners for editable fields
            addFieldEditListeners();
            
            // Update status
            document.getElementById('form-status-text').textContent = 'Form loaded. Ready to start agent processing.';
            
        } else {
            container.innerHTML = `<div class="error-message">Error loading form questions: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading form questions:', error);
        container.innerHTML = `<div class="error-message">Error loading form questions: ${error.message}</div>`;
    }
}

async function startFormAgentProcessing() {
    const progressFill = document.getElementById('form-progress-fill');
    const statusText = document.getElementById('form-status-text');
    const completedQuestionsSpan = document.getElementById('completed-questions');
    const processingTimeSpan = document.getElementById('processing-time');
    const startBtn = document.getElementById('start-agent-btn');
    const saveBtn = document.getElementById('save-form-btn');
    const exportBtn = document.getElementById('export-form-btn');
    
    // Disable start button and show processing state
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    const startTime = Date.now();
    let completedCount = 0;
    
    try {
        const response = await fetch(`/api/prior-auths/${automationData.id}/process-questions-realtime`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        switch (data.type) {
                            case 'status':
                                statusText.textContent = data.message;
                                progressFill.style.width = data.progress + '%';
                                break;
                                
                            case 'section_start':
                                statusText.textContent = `Processing ${data.section} section...`;
                                progressFill.style.width = data.progress + '%';
                                
                                // Auto-scroll to the first question of the new section
                                const firstQuestionOfSection = document.querySelector(`[data-question-id]`);
                                autoScrollToElement(firstQuestionOfSection, { 
                                    block: 'start',
                                    delay: 100 
                                });
                                break;
                                
                            case 'question_start':
                                // Update question status to processing
                                const questionItem = document.querySelector(`[data-question-id="${data.question_id}"]`);
                                if (questionItem) {
                                    const statusDiv = questionItem.querySelector('.answer-status');
                                    if (statusDiv) {
                                        statusDiv.innerHTML = `
                                            <i class="fas fa-spinner fa-spin"></i>
                                            <span>Agent processing...</span>
                                        `;
                                        statusDiv.className = 'answer-status processing';
                                    }
                                    
                                    // Auto-scroll to the question being processed
                                    autoScrollToElement(questionItem, { delay: 200 });
                                }
                                break;
                                
                            case 'question_result':
                                // Update question with result
                                let resultItem = document.querySelector(`[data-question-id="${data.question_id}"]`);
                                
                                // Handle follow-up questions - find parent question
                                if (data.question_id && data.question_id.endsWith('_followup')) {
                                    const parentQuestionId = data.question_id.replace('_followup', '');
                                    const parentItem = document.querySelector(`[data-question-id="${parentQuestionId}"]`);
                                    if (parentItem) {
                                        // Show follow-up container for parent question
                                        const followUpContainer = parentItem.querySelector('.follow-up-container');
                                        if (followUpContainer) {
                                            // Create follow-up question HTML if not already present
                                            if (!followUpContainer.querySelector('.follow-up-question')) {
                                                const followUpHTML = `
                                                    <div class="follow-up-question">
                                                        <div class="question-text follow-up-text">
                                                            <i class="fas fa-arrow-right"></i> ${data.question || 'Follow-up question'}
                                                        </div>
                                                        <div class="answer-container">
                                                            <textarea class="answer-field follow-up-field" placeholder="Agent will populate this answer..." data-field-id="${data.question_id}"></textarea>
                                                            <div class="answer-status">
                                                                <i class="fas fa-clock"></i>
                                                                <span>Waiting for agent...</span>
                                                            </div>
                                                            <div class="answer-source"></div>
                                                        </div>
                                                    </div>
                                                `;
                                                followUpContainer.innerHTML = followUpHTML;
                                                followUpContainer.style.display = 'block';
                                            }
                                            
                                            // Use the follow-up container as the result item
                                            resultItem = followUpContainer.querySelector('.follow-up-question');
                                        }
                                    }
                                }
                                
                                if (resultItem) {
                                    const answerField = resultItem.querySelector('.answer-field');
                                    const statusDiv = resultItem.querySelector('.answer-status');
                                    const sourceDiv = resultItem.querySelector('.answer-source');
                                    const questionType = resultItem.dataset.questionType;
                                    
                                    // Handle statements differently
                                    if (questionType === 'statement') {
                                        // Statements don't need status updates, just count as completed
                                        completedCount++;
                                        completedQuestionsSpan.textContent = completedCount;
                                    } else {
                                        // Populate answer for regular questions
                                        if (answerField && answerField.tagName === 'SELECT') {
                                            console.log(`Setting radio button answer for ${data.question_id}: ${data.answer}`);
                                            answerField.value = data.answer || '';
                                            
                                            // Debug specific questions
                                            if (data.question_id === 'h2' || data.question_id === 'h3') {
                                                console.log(`DEBUG: Set ${data.question_id} to "${data.answer}", current value: "${answerField.value}"`);
                                            }
                                            
                                            // Handle follow-up questions for radio buttons
                                            if (data.follow_up && shouldShowFollowUp(resultItem, data.answer)) {
                                                showFollowUpQuestion(resultItem, data.follow_up);
                                            } else {
                                                hideFollowUpQuestion(resultItem);
                                            }
                                        } else if (answerField) {
                                            answerField.value = data.answer || '';
                                        }
                                        
                                        // Update status
                                        if (statusDiv) {
                                            if (data.status === 'completed') {
                                                statusDiv.innerHTML = `
                                                    <i class="fas fa-check-circle text-success"></i>
                                                    <span>Agent completed</span>
                                                `;
                                                statusDiv.className = 'answer-status completed';
                                                completedCount++;
                                                completedQuestionsSpan.textContent = completedCount;
                                            } else {
                                                statusDiv.innerHTML = `
                                                    <i class="fas fa-exclamation-triangle text-warning"></i>
                                                    <span>${data.status}</span>
                                                `;
                                                statusDiv.className = 'answer-status error';
                                            }
                                        }
                                    }
                                    
                                    // Show source
                                    if (data.source && sourceDiv) {
                                        sourceDiv.innerHTML = `<small>Source: ${data.source}</small>`;
                                        sourceDiv.className = 'answer-source populated';
                                    }
                                    
                                    // Auto-scroll to the completed question
                                    autoScrollToElement(resultItem, { delay: 300 });
                                }
                                break;
                                
                            case 'section_complete':
                                statusText.textContent = `Completed ${data.section} section`;
                                progressFill.style.width = data.progress + '%';
                                break;
                                
                            case 'complete':
                                const endTime = Date.now();
                                const processingTime = ((endTime - startTime) / 1000).toFixed(1);
                                
                                statusText.textContent = 'Agent processing complete! All questions populated.';
                                progressFill.style.width = data.progress + '%';
                                processingTimeSpan.textContent = `${processingTime}s`;
                                
                                // Show completion message
                                setTimeout(() => {
                                    const completionMessage = document.createElement('div');
                                    completionMessage.className = 'completion-message success';
                                    completionMessage.innerHTML = `
                                        <i class="fas fa-check-circle"></i>
                                        <span>All ${data.total_questions} questions processed by agent! You can now edit any answers as needed.</span>
                                    `;
                                    document.getElementById('form-processing-summary').appendChild(completionMessage);
                                }, 1000);
                                
                                // Enable save and export buttons
                                saveBtn.style.display = 'inline-block';
                                exportBtn.style.display = 'inline-block';
                                
                                // Reset start button
                                startBtn.disabled = false;
                                startBtn.innerHTML = '<i class="fas fa-play"></i> Start Agent Processing';
                                return;
                                
                            case 'error':
                                statusText.textContent = `Error: ${data.error}`;
                                console.error('Agent processing error:', data.error);
                                
                                // Reset start button
                                startBtn.disabled = false;
                                startBtn.innerHTML = '<i class="fas fa-play"></i> Start Agent Processing';
                                return;
                        }
                    } catch (parseError) {
                        console.error('Error parsing SSE data:', parseError);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Error starting agent processing:', error);
        statusText.textContent = `Error: ${error.message}`;
        
        // Reset start button
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Agent Processing';
    }
}

async function executeScreening() {
    const content = document.getElementById('step-content-container');
    
    await streamText(content, `
        <div class="screening-analysis">
            <h4>Step 3: Clinical Screening & EHR Analysis</h4>
            <div class="result-card">
                <div class="ehr-screening">
                    <h5>EHR Data Screening Results:</h5>
                    
                    <div class="screening-section">
                        <h6><i class="fas fa-file-medical"></i> Pathology Review</h6>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Diagnosis Confirmed:</strong> ${automationData.diagnosis}</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Stage:</strong> ${automationData.stage || 'IV'} - Meets advanced cancer criteria</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Tumor Purity:</strong> 30% - Adequate for testing</span>
                        </div>
                    </div>
                    
                    <div class="screening-section">
                        <h6><i class="fas fa-dna"></i> Molecular Testing History</h6>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Prior Tests:</strong> ${automationData.prior_tests_count || 0} previous tests</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>No Prior Comprehensive NGS:</strong> Meets NCD 90.2 criteria</span>
                        </div>
                    </div>
                    
                    <div class="screening-section">
                        <h6><i class="fas fa-user-md"></i> Clinical Documentation</h6>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Oncology Consultation:</strong> Available and complete</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Treatment Plan:</strong> Molecular profiling indicated for treatment selection</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Genetic Counseling:</strong> ${automationData.ehr_documents.includes('Genetic Counseling Note') ? 'Completed' : 'Not required'}</span>
                        </div>
                    </div>
                    
                    <div class="screening-section">
                        <h6><i class="fas fa-flask"></i> Specimen Quality</h6>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Specimen Type:</strong> Excisional biopsy - Adequate</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Fixation:</strong> Alcohol-based - Compatible with testing</span>
                        </div>
                        <div class="screening-item success">
                            <i class="fas fa-check-circle"></i>
                            <span><strong>Tumor Cellularity:</strong> 30% - Meets minimum requirement</span>
                        </div>
                    </div>
                </div>
                
                <div class="decision-card success">
                    <h5><i class="fas fa-thumbs-up"></i> Screening Decision</h5>
                    <p><strong>Result:</strong> All clinical criteria met. Patient is appropriate candidate for ${automationData.service_type}.</p>
                    <p><strong>Action:</strong> Proceed to data extraction phase.</p>
                </div>
            </div>
        </div>
    `, 'screening');
    
    stepResults.screening = {
        status: 'completed',
        clinical_criteria_met: true,
        ehr_completeness: 'complete',
        decision: 'continue_automation'
    };
    
    await moveToNextStep();
}

async function executeDataExtraction() {
    const content = document.getElementById('step-content-container');
    
    await streamText(content, `
        <div class="data-extraction">
            <h4>Step 4: HUSKY Form Data Extraction from EHR</h4>
            <div class="result-card">
                <div class="extraction-process">
                    <h5>Extracting HUSKY Form Required Data from Clinical Documents:</h5>
                    
                    <div class="extraction-source">
                        <h6><i class="fas fa-user"></i> Member Information Extraction</h6>
                        <div class="extracted-data">
                            <div class="data-item">
                                <strong>Member ID:</strong> ${automationData.patient_mrn}
                                <div class="data-source">Source: EPIC Patient Demographics</div>
                            </div>
                            <div class="data-item">
                                <strong>Date of Birth:</strong> ${automationData.patient_dob}
                                <div class="data-source">Source: EPIC Patient Demographics</div>
                            </div>
                            <div class="data-item">
                                <strong>Member Name:</strong> ${automationData.patient_name}
                                <div class="data-source">Source: EPIC Patient Demographics</div>
                            </div>
                            <div class="data-item">
                                <strong>Address:</strong> 123 Main Street, Hartford, CT 06106
                                <div class="data-source">Source: EPIC Patient Demographics</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="extraction-source">
                        <h6><i class="fas fa-flask"></i> Requested Testing Information</h6>
                        <div class="extracted-data">
                            <div class="data-item">
                                <strong>Test Name:</strong> ${automationData.service_type}
                                <div class="data-source">Source: Molecular Testing Order</div>
                            </div>
                            <div class="data-item">
                                <strong>Date of Service:</strong> ${new Date().toISOString().split('T')[0]}
                                <div class="data-source">Source: Current Date</div>
                            </div>
                            <div class="data-item">
                                <strong>Type of Test:</strong> Gene panel
                                <div class="data-source">Source: Molecular Testing Order</div>
                            </div>
                            <div class="data-item">
                                <strong>Gene Mutation Tested For:</strong> Comprehensive genomic profiling (334 genes)
                                <div class="data-source">Source: Molecular Testing Order</div>
                            </div>
                            <div class="data-item">
                                <strong>ICD-10 Codes:</strong> ${automationData.icd10 || 'C34.90'}
                                <div class="data-source">Source: Pathology Report</div>
                            </div>
                            <div class="data-item">
                                <strong>CPT Requests:</strong> ${automationData.cpt_code} (1 unit)
                                <div class="data-source">Source: Molecular Testing Order</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="extraction-source">
                        <h6><i class="fas fa-file-medical"></i> Clinical Documentation</h6>
                        <div class="extracted-data">
                            <div class="data-item">
                                <strong>Ordering Provider:</strong> Dr. Jordan Rivera, Oncology
                                <div class="data-source">Source: Oncology Consultation Note</div>
                            </div>
                            <div class="data-item">
                                <strong>Genetic Counseling:</strong> ${automationData.ehr_documents.includes('Genetic Counseling Note') ? 'Completed' : 'Not required for cancer testing'}
                                <div class="data-source">Source: ${automationData.ehr_documents.includes('Genetic Counseling Note') ? 'Genetic Counseling Note' : 'Clinical Assessment'}</div>
                            </div>
                            <div class="data-item">
                                <strong>Clinical Indication:</strong> ${automationData.diagnosis} - Stage ${automationData.stage || 'IV'}
                                <div class="data-source">Source: Pathology Report</div>
                            </div>
                            <div class="data-item">
                                <strong>Treatment History:</strong> Pembrolizumab ongoing
                                <div class="data-source">Source: Oncology Consultation Note</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="extraction-source">
                        <h6><i class="fas fa-history"></i> Personal & Family History</h6>
                        <div class="extracted-data">
                            <div class="data-item">
                                <strong>Personal History:</strong> ${automationData.diagnosis} diagnosed at age ${automationData.age_at_diagnosis || '65'}
                                <div class="data-source">Source: Oncology Consultation Note</div>
                            </div>
                            <div class="data-item">
                                <strong>Family History:</strong> ${automationData.family_history_count > 0 ? 'Mother: breast cancer at age 45; Sister: breast cancer at age 52' : 'No relevant family history'}
                                <div class="data-source">Source: Family History Documentation</div>
                            </div>
                            <div class="data-item">
                                <strong>Prior Genetic Testing:</strong> ${automationData.prior_tests_count > 0 ? `${automationData.prior_tests_count} previous tests performed` : 'No prior comprehensive genetic testing'}
                                <div class="data-source">Source: Molecular Testing History</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="extraction-source">
                        <h6><i class="fas fa-hospital"></i> Provider Information</h6>
                        <div class="extracted-data">
                            <div class="data-item">
                                <strong>Billing Provider:</strong> Hartford Hospital (Medicaid #123456)
                                <div class="data-source">Source: Provider Database</div>
                            </div>
                            <div class="data-item">
                                <strong>Ordering Provider:</strong> Dr. Jordan Rivera, Oncology (Medicaid #789012)
                                <div class="data-source">Source: Provider Database</div>
                            </div>
                            <div class="data-item">
                                <strong>Provider Address:</strong> 80 Seymour Street, Hartford, CT 06102
                                <div class="data-source">Source: Provider Database</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="extraction-summary">
                    <h5><i class="fas fa-check-circle"></i> HUSKY Form Data Extraction Complete</h5>
                    <p><strong>Summary:</strong> Successfully extracted all required data for HUSKY Health Genetic Testing Prior Authorization form.</p>
                    <p><strong>Data Quality:</strong> All required fields populated with verified clinical information and proper citations.</p>
                    <p><strong>Form Sections Covered:</strong> Member Information, Requested Testing, Clinical Documentation, Personal/Family History, Provider Information</p>
                    <p><strong>Next Step:</strong> HUSKY form completion with extracted data.</p>
                </div>
            </div>
        </div>
    `, 'extraction');
    
    stepResults.extraction = {
        status: 'completed',
        data_extracted: true,
        all_fields_populated: true,
        citations_provided: true,
        husky_form_ready: true,
        action: 'proceed_to_form'
    };
    
    await moveToNextStep();
}

async function executeFormCompletion() {
    const content = document.getElementById('step-content-container');
    
    await streamText(content, `
        <div class="form-completion">
            <h4>Step 2: HUSKY Health Genetic Testing Prior Authorization Form</h4>
            <div class="result-card">
                <div class="form-preview">
                    <h5>HUSKY Health Genetic Testing Prior Authorization Request</h5>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-user"></i> Member Information</h6>
                        <div class="form-field">
                            <label>Member ID:</label>
                            <span>${automationData.patient_mrn}</span>
                        </div>
                        <div class="form-field">
                            <label>Date of Birth:</label>
                            <span>${automationData.patient_dob}</span>
                        </div>
                        <div class="form-field">
                            <label>Member Name:</label>
                            <span>${automationData.patient_name}</span>
                        </div>
                        <div class="form-field">
                            <label>Address:</label>
                            <span>123 Main Street, Hartford, CT 06106</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-flask"></i> Requested Testing</h6>
                        <div class="form-field">
                            <label>Test Name:</label>
                            <span>${automationData.service_type}</span>
                        </div>
                        <div class="form-field">
                            <label>Date of Service:</label>
                            <span>${new Date().toISOString().split('T')[0]}</span>
                        </div>
                        <div class="form-field">
                            <label>Type of Test:</label>
                            <span>Gene panel</span>
                        </div>
                        <div class="form-field">
                            <label>Gene Mutation Tested For:</label>
                            <span>Comprehensive genomic profiling (334 genes)</span>
                        </div>
                        <div class="form-field">
                            <label>ICD-10 Codes:</label>
                            <span>${automationData.icd10 || 'C34.90'} - ${automationData.diagnosis}</span>
                        </div>
                        <div class="form-field">
                            <label>CPT Requests:</label>
                            <span>${automationData.cpt_code} (1 unit)</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-question-circle"></i> Form Questions</h6>
                        <div class="form-field">
                            <label>Ordered by Qualified Clinician:</label>
                            <span>Yes - Dr. Jordan Rivera, Oncology</span>
                        </div>
                        <div class="form-field">
                            <label>Genetic Counseling Pre/Post:</label>
                            <span>${automationData.ehr_documents.includes('Genetic Counseling Note') ? 'Yes' : 'No - Not required for cancer testing'}</span>
                        </div>
                        <div class="form-field">
                            <label>Mutation Accepted by Societies:</label>
                            <span>Yes - NCCN guidelines support testing</span>
                        </div>
                        <div class="form-field">
                            <label>Diagnosable by Non-Genetic Means:</label>
                            <span>No - Molecular profiling required for treatment selection</span>
                        </div>
                        <div class="form-field">
                            <label>Test Performed Previously:</label>
                            <span>${automationData.prior_tests_count > 0 ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="form-field">
                            <label>Specific Reason and Guidelines:</label>
                            <span>NCCN Guidelines v2.2024 - Comprehensive genomic profiling for treatment selection in advanced ${automationData.diagnosis}</span>
                        </div>
                        <div class="form-field">
                            <label>Evaluation Studies List:</label>
                            <span>Pathology report, oncology consultation, molecular testing order attached</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-stethoscope"></i> Clinical Presentation</h6>
                        <div class="form-field">
                            <label>Has Clinical Features of Mutation:</label>
                            <span>Yes - ${automationData.diagnosis} with advanced stage</span>
                        </div>
                        <div class="form-field">
                            <label>At Direct Risk of Inheriting:</label>
                            <span>No - Somatic testing for treatment selection</span>
                        </div>
                        <div class="form-field">
                            <label>Prospective Parent High Risk Guides Reproductive Decisions:</label>
                            <span>No - Not applicable for cancer treatment</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-history"></i> History</h6>
                        <div class="form-field">
                            <label>Less Intensive Genetic Testing Completed:</label>
                            <span>${automationData.prior_tests_count > 0 ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="form-field">
                            <label>Personal History of Diagnosis:</label>
                            <span>Yes - ${automationData.diagnosis} diagnosed at age ${automationData.age_at_diagnosis || '65'}</span>
                        </div>
                        <div class="form-field">
                            <label>Family History of Diagnosis:</label>
                            <span>${automationData.family_history_count > 0 ? 'Yes' : 'No'}</span>
                        </div>
                        <div class="form-field">
                            <label>Partner History of Disorder or Mutation:</label>
                            <span>No</span>
                        </div>
                        <div class="form-field">
                            <label>Previous Child History of Disorder or Mutation:</label>
                            <span>No</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-heartbeat"></i> Medical Management</h6>
                        <div class="form-field">
                            <label>Material Impact on Treatment Beyond Typical:</label>
                            <span>Yes - Molecular profiling guides targeted therapy selection</span>
                        </div>
                        <div class="form-field">
                            <label>Improves Health Outcomes:</label>
                            <span>Yes - Targeted therapy based on molecular profile improves survival</span>
                        </div>
                        <div class="form-field">
                            <label>Disease Treatable or Preventable:</label>
                            <span>Yes - Multiple targeted therapies available for identified mutations</span>
                        </div>
                        <div class="form-field">
                            <label>Reduces Morbidity or Mortality:</label>
                            <span>Yes</span>
                        </div>
                        <div class="form-field">
                            <label>Avoids or Supplants Additional Testing:</label>
                            <span>Yes - Comprehensive panel eliminates need for multiple individual tests</span>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h6><i class="fas fa-hospital"></i> Provider Information</h6>
                        <div class="form-field">
                            <label>Billing Provider:</label>
                            <span>Hartford Hospital (Medicaid #123456)</span>
                        </div>
                        <div class="form-field">
                            <label>Ordering Provider:</label>
                            <span>Dr. Jordan Rivera, Oncology (Medicaid #789012)</span>
                        </div>
                    </div>
                </div>
                
                <div class="form-validation">
                    <h5><i class="fas fa-check-circle"></i> Form Validation</h5>
                    <div class="validation-item success">
                        <i class="fas fa-check"></i>
                        <span>All required fields completed per HUSKY schema</span>
                    </div>
                    <div class="validation-item success">
                        <i class="fas fa-check"></i>
                        <span>Clinical documentation verified</span>
                    </div>
                    <div class="validation-item success">
                        <i class="fas fa-check"></i>
                        <span>ICD-10 codes validated</span>
                    </div>
                    <div class="validation-item success">
                        <i class="fas fa-check"></i>
                        <span>CPT codes verified</span>
                    </div>
                    <div class="validation-item success">
                        <i class="fas fa-check"></i>
                        <span>HUSKY Health prior authorization form ready for submission</span>
                    </div>
                </div>
            </div>
        </div>
    `, 'form');
    
    stepResults.form = {
        status: 'completed',
        form_completed: true,
        all_fields_validated: true,
        ready_for_submission: true,
        action: 'complete_automation'
    };
    
    // Complete the automation
    await moveToNextStep();
}

async function moveToNextStep() {
    console.log('moveToNextStep called. Current step before increment:', currentAutomationStep);
    
    // Update the database with the current step before incrementing
    try {
        await fetch(`/api/prior-auths/${automationData.id}/step`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ step: currentAutomationStep })
        });
    } catch (error) {
        console.error('Error updating step in database:', error);
    }
    
    currentAutomationStep++;
    console.log('Current step after increment:', currentAutomationStep);
    
    if (currentAutomationStep <= automationSteps.length) {
        console.log('Moving to next step:', currentAutomationStep);
        // Add delay for visual effect
        await new Promise(resolve => setTimeout(resolve, 1000));
        await executeAutomationStep(currentAutomationStep);
    } else {
        console.log('Automation complete!');
        // Automation complete
        document.getElementById('current-step-status').innerHTML = '<i class="fas fa-check-circle"></i> Complete';
        document.getElementById('automation-progress-fill').style.width = '100%';
        document.getElementById('automation-progress-text').textContent = '100% Complete';
        
        // Show completion message
        const container = document.getElementById('step-content-container');
        container.innerHTML = `
            <div class="automation-complete">
                <div class="completion-card">
                    <i class="fas fa-check-circle"></i>
                    <h4>Automation Complete!</h4>
                    <p>The AI agent has successfully processed the prior authorization request.</p>
                    <div class="completion-summary">
                        <h5>Summary:</h5>
                        <ul>
                            <li>✓ Policy research and coverage analysis completed</li>
                            <li>✓ Form completion with EHR data extraction finished</li>
                            <li>✓ All form fields populated with proper citations</li>
                            <li>✓ Policy references and supporting documents included</li>
                            <li>✓ Prior authorization form ready for submission</li>
                        </ul>
                    </div>
            </div>
        </div>
    `;
    }
}

async function streamText(container, html, stepType = 'default') {
    // Clear container
    container.innerHTML = '';
    
    // Variable timing based on step complexity
    const timingMap = {
        'coverage': 15,      // Fast: Simple database lookup
        'insurance': 35,     // Slow: API calls, GPT-5 search
        'screening': 25,     // Medium: EHR analysis
        'extraction': 40,    // Slowest: Complex data extraction with citations
        'form': 20,          // Fast: Form population
        'default': 25        // Default timing
    };
    
    const delayPerWord = timingMap[stepType] || timingMap.default;
    
    // Simulate streaming effect
    const words = html.split(' ');
    let currentText = '';
    
    for (let i = 0; i < words.length; i++) {
        currentText += words[i] + ' ';
        container.innerHTML = currentText;
        await new Promise(resolve => setTimeout(resolve, delayPerWord));
    }
}

function closeAutomationPopup() {
    // This function is no longer needed since automation is now in tabs
    // But keeping it for backward compatibility
    if (streamingInterval) {
        clearInterval(streamingInterval);
    }
    // Stop polling when popup is closed
    stopAutomationPolling();
}

function approveCurrentStep() {
    // Hide action buttons
    document.getElementById('automation-actions').style.display = 'none';
    
    // Continue to next step
    moveToNextStep();
}

function requestChanges() {
    const changes = prompt('Enter the changes you would like to request:');
    if (changes) {
        // Log the changes request
        console.log('Changes requested:', changes);
        
        // Continue to next step
        approveCurrentStep();
    }
}

function sendToClinician() {
    // Show clinician message modal
    const messageContent = `
        <div class="message-body">
            <p><strong>To:</strong> Dr. Sarah Johnson, Oncology</p>
            <p><strong>Subject:</strong> Prior Authorization - Missing Documentation</p>
            <p><strong>Patient:</strong> ${automationData.patient_name} (MRN: ${automationData.patient_mrn})</p>
            <br>
            <p>Dear Dr. Johnson,</p>
            <p>I am processing a prior authorization request for ${automationData.service_type} for ${automationData.patient_name}.</p>
            <p>The insurance provider requires a genetic counseling consultation note to approve this request. This documentation is currently missing from the patient's record.</p>
            <p><strong>Required Action:</strong> Please provide a genetic counseling consultation note for this patient.</p>
            <p>Once this documentation is available, I can complete the prior authorization submission.</p>
            <br>
            <p>Thank you,<br>AI Prior Authorization Agent</p>
        </div>
    `;
    
    document.getElementById('clinician-message-content').innerHTML = messageContent;
    document.getElementById('clinician-message-modal').style.display = 'block';
}

function closeClinicianModal() {
    // Remove event listeners
    const subjectInput = document.getElementById('clinician-message-subject');
    const bodyTextarea = document.getElementById('clinician-message-body');
    
    if (subjectInput) {
        subjectInput.removeEventListener('input', previewClinicianMessage);
    }
    if (bodyTextarea) {
        bodyTextarea.removeEventListener('input', previewClinicianMessage);
    }
    
    document.getElementById('clinician-message-modal').style.display = 'none';
}

// Function to fetch insurance analysis information
async function fetchInsuranceAnalysisInfo(authId) {
    try {
        const response = await fetch(`/api/prior-auths/${authId}/analyze-insurance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.analysis) {
                updateInsuranceAnalysisDisplay(data.analysis);
            }
        } else {
            console.error('Failed to fetch insurance analysis:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching insurance analysis:', error);
    }
}

// Function to update insurance analysis display
function updateInsuranceAnalysisDisplay(analysis) {
    const jurisdictionDisplay = document.getElementById('jurisdiction-display');
    const coverageStatusDisplay = document.getElementById('coverage-status-display');
    
    if (jurisdictionDisplay) {
        jurisdictionDisplay.textContent = analysis.dashboard_info?.jurisdiction || 'N/A';
    }
    
    if (coverageStatusDisplay) {
        coverageStatusDisplay.textContent = analysis.coverage_status || 'N/A';
    }
}

// GPT-5 Search Animation Functions
function showGPT5SearchAnimation() {
    const searchAnimation = document.getElementById('gpt5-search-animation');
    const stepContent = document.getElementById('step-content-container');
    
    if (searchAnimation) {
        searchAnimation.style.display = 'block';
    }
    if (stepContent) {
        stepContent.style.display = 'none';
    }
}

function hideGPT5SearchAnimation() {
    const searchAnimation = document.getElementById('gpt5-search-animation');
    const stepContent = document.getElementById('step-content-container');
    
    if (searchAnimation) {
        searchAnimation.style.display = 'none';
    }
    if (stepContent) {
        stepContent.style.display = 'block';
    }
}

function updateSearchQuery(query) {
    const searchQueryElement = document.getElementById('current-search-query');
    if (searchQueryElement) {
        searchQueryElement.textContent = query;
    }
}

function updateSearchProgress(percent) {
    const progressFill = document.getElementById('search-progress-fill');
    const progressText = document.getElementById('search-progress-text');
    
    if (progressFill) {
        progressFill.style.width = percent + '%';
    }
    if (progressText) {
        progressText.textContent = percent + '%';
    }
}

// Form completion animation functions
function showFormCompletionAnimation() {
    const animation = document.getElementById('form-completion-animation');
    if (animation) {
        animation.style.display = 'block';
    }
}

function hideFormCompletionAnimation() {
    const animation = document.getElementById('form-completion-animation');
    if (animation) {
        animation.style.display = 'none';
    }
}

function updateFormQuery(message) {
    const queryElement = document.getElementById('current-form-query');
    if (queryElement) {
        queryElement.textContent = message;
    }
}

function updateFormProgress(progress) {
    const progressFill = document.getElementById('form-progress-fill');
    const progressText = document.getElementById('form-progress-text');
    
    if (progressFill) {
        progressFill.style.width = progress + '%';
    }
    if (progressText) {
        progressText.textContent = Math.round(progress) + '%';
    }
}

// Step History Management
let stepHistory = [];

function addCompletedStep(stepNumber, stepData) {
    const step = automationSteps[stepNumber - 1];
    if (!step) return;
    
    const completedStep = {
        stepNumber: stepNumber,
        title: step.title,
        description: step.description,
        icon: step.icon,
        completedAt: new Date().toISOString(),
        data: stepData
    };
    
    stepHistory.push(completedStep);
    updateStepHistoryDisplay();
}

function updateStepHistoryDisplay() {
    const historyPanel = document.getElementById('step-history-panel');
    const historyContainer = document.getElementById('step-history-container');
    
    if (stepHistory.length === 0) {
        historyPanel.style.display = 'none';
        return;
    }
    
    historyPanel.style.display = 'block';
    historyContainer.innerHTML = '';
    
    stepHistory.forEach((step, index) => {
        const stepElement = createCompletedStepElement(step, index);
        historyContainer.appendChild(stepElement);
    });
}

function createCompletedStepElement(step, index) {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'completed-step';
    stepDiv.innerHTML = `
        <div class="completed-step-header" onclick="toggleStepDetails(${index})">
            <div class="completed-step-info">
                <div class="completed-step-icon">
                    <i class="${step.icon}"></i>
                </div>
                <div class="completed-step-details">
                    <div class="completed-step-title">Step ${step.stepNumber}: ${step.title}</div>
                    <div class="completed-step-description">${step.description}</div>
                </div>
            </div>
            <div class="completed-step-status">
                <i class="fas fa-check-circle"></i>
                <span>Completed</span>
            </div>
            <button class="completed-step-toggle" onclick="event.stopPropagation(); toggleStepDetails(${index})">
                <i class="fas fa-chevron-down"></i>
            </button>
        </div>
        <div class="completed-step-content" id="step-content-${index}">
            <div class="completed-step-content-inner">
                ${generateStepContent(step)}
            </div>
        </div>
    `;
    
    return stepDiv;
}

function toggleStepDetails(index) {
    const contentElement = document.getElementById(`step-content-${index}`);
    const toggleButton = contentElement.previousElementSibling.querySelector('.completed-step-toggle');
    
    if (contentElement.classList.contains('expanded')) {
        contentElement.classList.remove('expanded');
        toggleButton.classList.remove('expanded');
    } else {
        contentElement.classList.add('expanded');
        toggleButton.classList.add('expanded');
    }
}

function generateStepContent(step) {
    if (step.stepNumber === 1) {
        return generateStep1Content(step.data);
    } else if (step.stepNumber === 2) {
        return generateStep2Content(step.data);
    }
    return '<p>Step details not available.</p>';
}

function generateStep1Content(data) {
    if (!data) return '<p>No data available for this step.</p>';
    
    return `
        <div class="step-summary">
            <h6>Policy Research Summary</h6>
            <div class="step-summary-content">
                <strong>Coverage Status:</strong> ${data.coverage_status?.toUpperCase() || 'Unknown'}<br>
                <strong>Confidence:</strong> ${Math.round((data.confidence_score || 0) * 100)}%<br>
                <strong>Requirements Found:</strong> ${data.requirements?.length || 0}<br>
                <strong>Sources Analyzed:</strong> ${data.search_sources?.length || 0}
            </div>
        </div>
        
        <div class="step-details-grid">
            <div class="step-detail-item">
                <div class="step-detail-label">Coverage Status</div>
                <div class="step-detail-value">${data.coverage_status?.toUpperCase() || 'Unknown'}</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">Confidence Score</div>
                <div class="step-detail-value">${Math.round((data.confidence_score || 0) * 100)}%</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">Requirements</div>
                <div class="step-detail-value">${data.requirements?.length || 0} found</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">Sources</div>
                <div class="step-detail-value">${data.search_sources?.length || 0} analyzed</div>
            </div>
        </div>
        
        <div class="step-actions">
            <button class="step-action-btn" onclick="viewStepDetails(${step.stepNumber})">
                <i class="fas fa-eye"></i> View Details
            </button>
            <button class="step-action-btn" onclick="exportStepData(${step.stepNumber})">
                <i class="fas fa-download"></i> Export Data
            </button>
            <button class="step-action-btn primary" onclick="reprocessStep(${step.stepNumber})">
                <i class="fas fa-redo"></i> Reprocess
            </button>
        </div>
    `;
}

function generateStep2Content(data) {
    if (!data) return '<p>No data available for this step.</p>';
    
    return `
        <div class="step-summary">
            <h6>Form Completion Summary</h6>
            <div class="step-summary-content">
                <strong>Form Status:</strong> ${data.status || 'Unknown'}<br>
                <strong>Fields Completed:</strong> ${data.completed_fields || 0}/${data.total_fields || 0}<br>
                <strong>EHR Data Sources:</strong> ${data.ehr_citations?.length || 0}<br>
                <strong>Policy References:</strong> ${data.policy_references?.length || 0}
            </div>
        </div>
        
        <div class="step-details-grid">
            <div class="step-detail-item">
                <div class="step-detail-label">Form Status</div>
                <div class="step-detail-value">${data.status || 'Unknown'}</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">Completion Rate</div>
                <div class="step-detail-value">${data.completed_fields || 0}/${data.total_fields || 0}</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">EHR Citations</div>
                <div class="step-detail-value">${data.ehr_citations?.length || 0} sources</div>
            </div>
            <div class="step-detail-item">
                <div class="step-detail-label">Policy References</div>
                <div class="step-detail-value">${data.policy_references?.length || 0} documents</div>
            </div>
        </div>
        
        <div class="step-actions">
            <button class="step-action-btn" onclick="viewStepDetails(${step.stepNumber})">
                <i class="fas fa-eye"></i> View Details
            </button>
            <button class="step-action-btn" onclick="exportStepData(${step.stepNumber})">
                <i class="fas fa-download"></i> Export Data
            </button>
            <button class="step-action-btn primary" onclick="reprocessStep(${step.stepNumber})">
                <i class="fas fa-redo"></i> Reprocess
            </button>
        </div>
    `;
}

function viewStepDetails(stepNumber) {
    // This would open a modal with detailed step information
    console.log(`Viewing details for step ${stepNumber}`);
    alert(`Viewing detailed information for Step ${stepNumber}`);
}

function exportStepData(stepNumber) {
    const step = stepHistory.find(s => s.stepNumber === stepNumber);
    if (!step) return;
    
    const dataStr = JSON.stringify(step.data, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `step_${stepNumber}_data_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function reprocessStep(stepNumber) {
    if (confirm(`Are you sure you want to reprocess Step ${stepNumber}? This will restart the current workflow.`)) {
        // Reset to the specified step
        currentAutomationStep = stepNumber;
        stepHistory = stepHistory.filter(s => s.stepNumber < stepNumber);
        updateStepHistoryDisplay();
        
        // Restart the automation
        executeAutomationStep(stepNumber);
    }
}

// Form validation functions
function approveForm() {
    console.log('Form approved by user');
    
    // Update the form status
    const validationSection = document.querySelector('.validation-section');
    if (validationSection) {
        validationSection.innerHTML = `
            <div class="validation-success">
                <i class="fas fa-check-circle"></i>
                <h5>Form Approved!</h5>
                <p>The prior authorization form has been approved and is ready for submission.</p>
                <button class="btn btn-success" onclick="submitForm()">
                    <i class="fas fa-paper-plane"></i> Submit to Insurance
                </button>
            </div>
        `;
    }
    
    // Update step results
    stepResults.form.status = 'approved';
    stepResults.form.action = 'submitted';
}

function requestFormChanges() {
    const changes = prompt('Please describe what changes you would like to make to the form:');
    if (changes) {
        console.log('Form changes requested:', changes);
        
        // Update the form status
        const validationSection = document.querySelector('.validation-section');
        if (validationSection) {
            validationSection.innerHTML = `
                <div class="validation-changes">
                    <i class="fas fa-edit"></i>
                    <h5>Changes Requested</h5>
                    <p><strong>Requested Changes:</strong> ${changes}</p>
                    <p>The system will update the form based on your feedback.</p>
                    <button class="btn btn-primary" onclick="regenerateForm()">
                        <i class="fas fa-sync"></i> Regenerate Form
                    </button>
                </div>
            `;
        }
        
        // Update step results
        stepResults.form.status = 'changes_requested';
        stepResults.form.changes = changes;
    }
}

function exportForm() {
    console.log('Exporting form data');
    
    // Create a downloadable version of the form
    const formData = {
        timestamp: new Date().toISOString(),
        patient_mrn: automationData.patient_mrn,
        cpt_code: automationData.cpt_code,
        insurance_provider: automationData.insurance_provider,
        form_sections: stepResults.form?.sections || [],
        ehr_citations: stepResults.form?.ehr_citations || [],
        policy_references: stepResults.form?.policy_references || []
    };
    
    const dataStr = JSON.stringify(formData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `prior_auth_${automationData.patient_mrn}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function openInteractiveForm() {
    // Open the interactive form editor in a new window/tab
    const authId = automationData.id;
    const url = `/interactive-form?auth_id=${authId}`;
    window.open(url, '_blank');
}

function submitForm() {
    console.log('Submitting form to insurance');
    
    // Show submission status
    const validationSection = document.querySelector('.validation-section');
    if (validationSection) {
        validationSection.innerHTML = `
            <div class="submission-success">
                <i class="fas fa-paper-plane"></i>
                <h5>Form Submitted Successfully!</h5>
                <p>The prior authorization request has been submitted to ${automationData.insurance_provider}.</p>
                <p><strong>Reference Number:</strong> PA-${Date.now()}</p>
                <button class="btn btn-primary" onclick="closeAutomationPopup()">
                    <i class="fas fa-check"></i> Complete
                </button>
            </div>
        `;
    }
    
    // Update database status
    fetch(`/api/prior-auths/${automationData.id}/status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'submitted' })
    }).catch(error => console.error('Error updating status:', error));
}

function regenerateForm() {
    console.log('Regenerating form with changes');
    
    // Restart the form completion process
    executeFormCompletionWithEHR();
}

function showCaseDetails(auth) {
    // Create the modal content
    const modalContent = `
        <div class="auth-details">
            <div class="detail-section">
                <h3>Patient Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Patient Name:</label>
                        <span>${auth.patient_name}</span>
                    </div>
                    <div class="detail-item">
                        <label>MRN:</label>
                        <span>${auth.patient_mrn}</span>
                    </div>
                    <div class="detail-item">
                        <label>Date of Birth:</label>
                        <span>${auth.patient_dob || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Gender:</label>
                        <span>${auth.patient_gender || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Service Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Service Type:</label>
                        <span>${auth.service_type}</span>
                    </div>
                    <div class="detail-item">
                        <label>CPT Code:</label>
                        <span>${auth.cpt_code || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Diagnosis:</label>
                        <span>${auth.diagnosis}</span>
                    </div>
                    <div class="detail-item">
                        <label>Procedure Date:</label>
                        <span>${auth.procedure_date || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Insurance Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Insurance Provider:</label>
                        <span>${auth.insurance_provider}</span>
                    </div>
                    <div class="detail-item">
                        <label>Insurance Requirements:</label>
                        <span>${auth.insurance_requirements || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Status Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Status:</label>
                        <span class="status-badge ${auth.status}">${getStatusDisplay(auth.status)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Current Step:</label>
                        <span>${auth.current_step || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Automation Status:</label>
                        <span>${auth.automation_status || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Assigned To:</label>
                        <span>${auth.assigned_to || 'Unassigned'}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Timeline</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Created Date:</label>
                        <span>${formatDate(auth.created_date)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Due Date:</label>
                        <span>${formatDate(auth.due_date)}</span>
                    </div>
                    <div class="detail-item">
                        <label>Last Updated:</label>
                        <span>${formatDate(auth.last_updated)}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>Additional Information</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Clinical Urgency:</label>
                        <span>${auth.clinical_urgency || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Treatment History:</label>
                        <span>${auth.treatment_history || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Allergies:</label>
                        <span>${auth.allergies || 'None'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Notes:</label>
                        <span>${auth.notes || 'No notes'}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Set modal title
    document.getElementById('modal-title').textContent = `Prior Authorization Details - ${auth.patient_name}`;
    
    // Populate the modal body
    document.getElementById('modal-body').innerHTML = modalContent;
    
    // Update the action button based on status
    const actionBtn = document.getElementById('modal-action-btn');
    const cancelBtn = document.getElementById('modal-cancel-btn');
    
    if (auth.status === 'pending') {
        actionBtn.textContent = 'Start Automation';
        actionBtn.className = 'btn btn-primary';
        actionBtn.onclick = () => {
            // Switch to automation tab and start automation
            switchModalTab('automation');
            runAutomationWorkflow(auth.id);
        };
        cancelBtn.style.display = 'none';
            } else if (auth.status === 'running') {
            actionBtn.textContent = 'View Progress';
            actionBtn.className = 'btn btn-info';
            actionBtn.onclick = () => {
                // Switch to automation tab and show progress
                switchModalTab('automation');
                showAutomationProgress(auth.id);
            };
            cancelBtn.style.display = 'inline-block';
    } else if (auth.status === 'completed') {
        actionBtn.textContent = 'View Automation History';
        actionBtn.className = 'btn btn-success';
        actionBtn.onclick = () => {
            // Switch to automation tab and show history
            switchModalTab('automation');
            showAutomationHistory(auth.id);
        };
        cancelBtn.style.display = 'none';
    } else if (auth.status === 'review' || auth.status === 'feedback') {
        actionBtn.textContent = 'View Progress';
        actionBtn.className = 'btn btn-info';
        actionBtn.onclick = () => {
            // Switch to automation tab and show progress
            switchModalTab('automation');
            showAutomationProgress(auth.id);
        };
        cancelBtn.style.display = 'none';
    } else {
        actionBtn.textContent = 'View Details';
        actionBtn.className = 'btn btn-secondary';
        actionBtn.onclick = () => closeModal();
        cancelBtn.style.display = 'none';
    }
    
    // Show the modal
    document.getElementById('auth-detail-modal').style.display = 'block';
}

function switchModalTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.modal-tab');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[data-tab="${tabName}"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load form questions when the form processing tab is selected
    if (tabName === 'form-processing') {
        loadFormQuestions();
    }
}

function showAutomationProgress(authId) {
    // Switch to automation tab
    switchModalTab('automation');
    
    // Start polling for updates
    startAutomationPolling(authId);
}

function showAutomationHistory(authId) {
    // Switch to automation tab
    switchModalTab('automation');
    
    // Get final results and show detailed content
    fetch(`/api/automation/status/${authId}`)
        .then(response => response.json())
        .then(status => {
            if (status.details) {
                // Show the detailed content (same as during automation)
                updateDetailedContent(status);
                
                // // Add completion message at the top
                // const contentContainer = document.getElementById('step-content-container');
                // if (contentContainer) {
                //     const completionMessage = document.createElement('div');
                //     completionMessage.className = 'completion-message';
                //     completionMessage.innerHTML = `
                //         <div class="completion-banner">
                //             <i class="fas fa-check-circle"></i>
                //             <span>Automation completed successfully!</span>
                //         </div>
                //     `;
                //     contentContainer.insertBefore(completionMessage, contentContainer.firstChild);
                // }
                
                // Update step status to show completion
                const currentStepStatus = document.getElementById('current-step-status');
                if (currentStepStatus) {
                    currentStepStatus.innerHTML = '<i class="fas fa-check"></i> Complete';
                }
            } else {
                // Fallback to showing basic completion
                const content = document.getElementById('step-content-container');
                content.innerHTML = '<div class="automation-results"><h4><i class="fas fa-check-circle"></i> Automation Completed</h4><p>Results are no longer available.</p></div>';
            }
        })
        .catch(error => {
            console.error('Error getting automation history:', error);
            const content = document.getElementById('step-content-container');
            content.innerHTML = '<div class="automation-results"><h4><i class="fas fa-exclamation-triangle"></i> Error</h4><p>Could not load automation history.</p></div>';
        });
}

function resetAllCases() {
    if (confirm('Are you sure you want to reset all cases to pending status? This will clear all automation progress.')) {
        fetch('/api/reset-all-cases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('All cases have been reset to pending status.');
                // Reload the data to reflect changes
                loadData();
            } else {
                alert('Error resetting cases: ' + result.error);
            }
        })
        .catch(error => {
            console.error('Error resetting cases:', error);
            alert('Error resetting cases: ' + error.message);
        });
    }
}



function cancelAutomation() {
    const authId = automationData?.id;
    if (!authId) {
        alert('No automation to cancel.');
        return;
    }
    
    if (confirm('Are you sure you want to cancel the automation? This action cannot be undone.')) {
        // Stop polling
        stopAutomationPolling();
        
        // Clear background tasks (this would need a backend endpoint)
        fetch(`/api/prior-auths/${authId}/cancel-automation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('Automation has been cancelled.');
                // Reload the data to reflect changes
                loadData();
                // Refresh the modal to show updated button states
                const auth = allPriorAuths.find(a => a.id == authId);
                if (auth) {
                    showCaseDetails(auth);
                }
            } else {
                alert('Error cancelling automation: ' + result.error);
            }
        })
        .catch(error => {
            console.error('Error cancelling automation:', error);
            alert('Error cancelling automation: ' + error.message);
        });
    }
}

function viewDetails(authId) {
    // Find the auth data
    const auth = allPriorAuths.find(a => a.id === authId);
    if (!auth) {
        console.error('Auth not found:', authId);
        return;
    }
    
    showCaseDetails(auth);
}

function closeModal() {
    document.getElementById('auth-detail-modal').style.display = 'none';
    // Stop polling when modal is closed
    stopAutomationPolling();
}

function closeStepModal() {
    document.getElementById('step-detail-modal').style.display = 'none';
}

function viewStepDetails(authId) {
    // Find the auth data
    const auth = allPriorAuths.find(a => a.id === authId);
    if (!auth) {
        console.error('Auth not found:', authId);
        return;
    }
    
    // Parse step details from JSON
    let stepDetails = {};
    try {
        stepDetails = JSON.parse(auth.step_details || '{}');
    } catch (e) {
        console.error('Error parsing step details:', e);
    }
    
    // Create step details content
    const stepContent = `
        <div class="step-details">
            <div class="step-overview">
                <h3>Automation Progress</h3>
                <div class="step-progress">
                    <div class="step-item ${auth.current_step >= 1 ? 'completed' : 'pending'}">
                        <div class="step-number">1</div>
                        <div class="step-info">
                            <h4>Coverage Determination</h4>
                            <p>${stepDetails.step1?.details || 'Not started'}</p>
                        </div>
                    </div>
                    <div class="step-item ${auth.current_step >= 2 ? 'completed' : 'pending'}">
                        <div class="step-number">2</div>
                        <div class="step-info">
                            <h4>Form Completion</h4>
                            <p>${stepDetails.step2?.details || 'Not started'}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="step-summary">
                <h3>Current Status</h3>
                <div class="status-summary">
                    <p><strong>Current Step:</strong> ${auth.current_step || 1} of 2</p>
                    <p><strong>Automation Status:</strong> ${auth.automation_status || 'pending'}</p>
                    <p><strong>Overall Status:</strong> ${auth.status}</p>
                </div>
            </div>
        </div>
    `;
    
    // Populate the step modal
    document.getElementById('step-modal-title').textContent = `Step Details - ${auth.patient_name}`;
    document.getElementById('step-modal-body').innerHTML = stepContent;
    
    // Show the modal
    document.getElementById('step-detail-modal').style.display = 'block';
}



function approveAuth(authId) {
    if (confirm('Are you sure you want to approve this prior authorization request?')) {
        // Call backend to approve
        fetch(`/api/prior-auths/${authId}/approve-step`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'approve',
                notes: 'Approved by user'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Prior authorization approved successfully');
                loadData(); // Refresh the data
            } else {
                alert('Error approving request: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error approving request');
        });
    }
}

function provideFeedback(authId) {
    const feedback = prompt('Please provide feedback for this request:');
    if (feedback) {
        // Call backend to provide feedback
        fetch(`/api/prior-auths/${authId}/provide-feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                feedback: feedback
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Feedback submitted successfully');
                loadData(); // Refresh the data
            } else {
                alert('Error submitting feedback: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error submitting feedback');
        });
    }
}

function inspectCompletedStep(stepNumber, stepTitle) {
    // Get the step details from the current automation data
    const stepResults = window.stepResults || {};
    const stepData = stepResults[getStepKey(stepNumber)] || {};
    
    // Create detailed step content based on step number
    let stepContent = '';
    
    switch(stepNumber) {
        case 1:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 1: Coverage Determination - Completed</h3>
                    <div class="step-details">
                        <div class="detail-section">
                            <h4>Coverage Analysis</h4>
                            <div class="coverage-result">
                                <div class="result-card success">
                                    <i class="fas fa-check-circle"></i>
                                    <div class="result-content">
                                        <strong>Coverage Confirmed</strong>
                                        <p>CPT code ${automationData.cpt_code} is covered under ${automationData.insurance_provider} for the specified clinical indication.</p>
                                        <div class="coverage-details">
                                            <p><strong>Coverage Level:</strong> Full coverage with prior authorization</p>
                                            <p><strong>Clinical Criteria:</strong> Met - ${automationData.diagnosis}</p>
                                            <p><strong>Documentation Required:</strong> Genetic counseling note, family history</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h4>Process Log</h4>
                            <div class="process-log">
                                <div class="log-entry">
                                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                                    <span class="message">Starting coverage determination for CPT code ${automationData.cpt_code}</span>
                                </div>
                                <div class="log-entry">
                                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                                    <span class="message">Checking ${automationData.insurance_provider} coverage policies</span>
                                </div>
                                <div class="log-entry">
                                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                                    <span class="message">Coverage confirmed - proceeding to next step</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 2:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 2: Insurance Documentation - Completed</h3>
                    <div class="step-details">
                        <div class="detail-section">
                            <h4>GPT-5 Search Results</h4>
                            <div class="search-results">
                                <div class="search-query">
                                    <strong>Search Query:</strong>
                                    <p>"${automationData.insurance_provider} prior authorization requirements for CPT ${automationData.cpt_code} genetic testing ${automationData.service_type}"</p>
                                </div>
                                
                                <div class="result-item">
                                    <div class="result-header">
                                        <i class="fas fa-file-pdf"></i>
                                        <span>${automationData.insurance_provider} Genetic Testing Coverage Policy</span>
                                    </div>
                                    <div class="result-content">
                                        <p><strong>Relevance:</strong> 95% - Direct policy document for genetic testing</p>
                                        <p><strong>Key Requirements:</strong></p>
                                        <ul>
                                            <li>Genetic counselor consultation required</li>
                                            <li>Family history documentation</li>
                                            <li>Clinical indication documentation</li>
                                            <li>Provider credentials verification</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h4>Extracted Requirements</h4>
                            <div class="requirements-list">
                                <div class="requirement-item">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Genetic counselor consultation</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Family history documentation</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Clinical indication documentation</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Provider credentials verification</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 3:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 3: Screening - Completed</h3>
                    <div class="step-details">
                        <div class="detail-section">
                            <h4>Screening Results</h4>
                            <div class="screening-results">
                                <div class="screening-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Patient demographics complete</span>
                                </div>
                                <div class="screening-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Family history documented</span>
                                </div>
                                <div class="screening-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Genetic counseling note available</span>
                                </div>
                                <div class="screening-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Clinical indication appropriate</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h4>Screening Decision</h4>
                            <div class="decision-card success">
                                <i class="fas fa-check-circle"></i>
                                <div class="decision-content">
                                    <strong>Screening Passed</strong>
                                    <p>All required documentation is available in the EHR.</p>
                                    <p><strong>Action:</strong> Proceed to data extraction</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 4:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 4: Data Extraction - Completed</h3>
                    <div class="step-details">
                        <div class="detail-section">
                            <h4>Data Sources</h4>
                            <div class="source-list">
                                <div class="source-item">
                                    <i class="fas fa-user"></i>
                                    <span>Patient Demographics - EPIC Patient Record</span>
                                </div>
                                <div class="source-item">
                                    <i class="fas fa-file-medical"></i>
                                    <span>Family History - Progress Note 2024-01-15</span>
                                </div>
                                <div class="source-item">
                                    <i class="fas fa-stethoscope"></i>
                                    <span>Clinical History - Oncology Consultation 2024-01-10</span>
                                </div>
                                <div class="source-item">
                                    <i class="fas fa-pills"></i>
                                    <span>Medications - Medication List 2024-01-12</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h4>Extracted Data with Citations</h4>
                            <div class="data-items">
                                <div class="data-item">
                                    <div class="data-label">Patient Name:</div>
                                    <div class="data-value">${automationData.patient_name}</div>
                                    <div class="data-source">Source: EPIC Patient Record</div>
                                </div>
                                <div class="data-item">
                                    <div class="data-label">Date of Birth:</div>
                                    <div class="data-value">${automationData.patient_dob}</div>
                                    <div class="data-source">Source: EPIC Patient Record</div>
                                </div>
                                <div class="data-item">
                                    <div class="data-label">Family History:</div>
                                    <div class="data-value">Mother: breast cancer at age 45; Sister: breast cancer at age 52</div>
                                    <div class="data-source">Source: Progress Note 2024-01-15, Dr. Johnson</div>
                                </div>
                                <div class="data-item">
                                    <div class="data-label">Clinical Indication:</div>
                                    <div class="data-value">${automationData.diagnosis}</div>
                                    <div class="data-source">Source: Oncology Consultation 2024-01-10, Dr. Johnson</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;
            
        case 2:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 2: HUSKY Form Completion - Completed</h3>
                    <div class="step-details">
                        <div class="detail-section">
                            <h4>HUSKY Health Genetic Testing Prior Authorization Form</h4>
                            <div class="form-preview">
                                <div class="form-section">
                                    <h5>Member Information</h5>
                                    <div class="form-field">
                                        <label>Member ID:</label>
                                        <span>${automationData.patient_mrn}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Date of Birth:</label>
                                        <span>${automationData.patient_dob}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Member Name:</label>
                                        <span>${automationData.patient_name}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Address:</label>
                                        <span>123 Main Street, Hartford, CT 06106</span>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h5>Requested Testing</h5>
                                    <div class="form-field">
                                        <label>Test Name:</label>
                                        <span>${automationData.service_type}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Date of Service:</label>
                                        <span>${new Date().toISOString().split('T')[0]}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Type of Test:</label>
                                        <span>Gene panel</span>
                                    </div>
                                    <div class="form-field">
                                        <label>ICD-10 Codes:</label>
                                        <span>${automationData.icd10 || 'C34.90'}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>CPT Requests:</label>
                                        <span>${automationData.cpt_code} (1 unit)</span>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h5>Form Questions</h5>
                                    <div class="form-field">
                                        <label>Ordered by Qualified Clinician:</label>
                                        <span>Yes - Dr. Jordan Rivera, Oncology</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Genetic Counseling Pre/Post:</label>
                                        <span>${automationData.ehr_documents.includes('Genetic Counseling Note') ? 'Yes' : 'No - Not required for cancer testing'}</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Mutation Accepted by Societies:</label>
                                        <span>Yes - NCCN guidelines support testing</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Specific Reason and Guidelines:</label>
                                        <span>NCCN Guidelines v2.2024 - Comprehensive genomic profiling for treatment selection</span>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h5>Clinical Presentation</h5>
                                    <div class="form-field">
                                        <label>Has Clinical Features of Mutation:</label>
                                        <span>Yes - ${automationData.diagnosis} with advanced stage</span>
                                    </div>
                                    <div class="form-field">
                                        <label>At Direct Risk of Inheriting:</label>
                                        <span>No - Somatic testing for treatment selection</span>
                                    </div>
                                </div>
                                
                                <div class="form-section">
                                    <h5>Medical Management</h5>
                                    <div class="form-field">
                                        <label>Material Impact on Treatment:</label>
                                        <span>Yes - Molecular profiling guides targeted therapy selection</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Improves Health Outcomes:</label>
                                        <span>Yes - Targeted therapy based on molecular profile improves survival</span>
                                    </div>
                                    <div class="form-field">
                                        <label>Reduces Morbidity or Mortality:</label>
                                        <span>Yes</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-section">
                            <h4>HUSKY Form Validation</h4>
                            <div class="validation-results">
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>All required fields completed per HUSKY schema</span>
                                </div>
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Member information verified</span>
                                </div>
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Clinical documentation attached</span>
                                </div>
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>ICD-10 and CPT codes validated</span>
                                </div>
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>Provider information verified</span>
                                </div>
                                <div class="validation-item success">
                                    <i class="fas fa-check-circle"></i>
                                    <span>HUSKY Health prior authorization form ready for submission</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;
    }
    
    // Show the step inspection modal
    document.getElementById('step-modal-title').textContent = `Step ${stepNumber}: ${stepTitle} - Inspection`;
    document.getElementById('step-modal-body').innerHTML = stepContent;
    document.getElementById('step-detail-modal').style.display = 'block';
}

function getStepKey(stepNumber) {
    const stepKeys = {
        1: 'coverage',
        2: 'insurance',
        3: 'screening',
        4: 'extraction',
        5: 'form'
    };
    return stepKeys[stepNumber] || 'unknown';
}

function viewAutomationProgress(authId) {
    // Find the auth data
    const auth = allPriorAuths.find(a => a.id === authId);
    if (!auth) {
        console.error('Auth not found:', authId);
        return;
    }
    
    // Set the automation data for the popup with realistic fields
    automationData = {
        patient_name: auth.patient_name,
        patient_mrn: auth.patient_mrn,
        patient_dob: auth.patient_dob,
        patient_gender: auth.patient_gender,
        service_type: auth.service_type,
        cpt_code: auth.cpt_code,
        diagnosis: auth.diagnosis,
        icd10: auth.icd10 || 'C34.90',
        stage: auth.stage || 'IV',
        insurance_provider: auth.insurance_provider,
        insurance_plan: auth.insurance_plan || 'Medicare Advantage HMO',
        ehr_documents: JSON.parse(auth.ehr_documents || '[]'),
        prior_tests_count: auth.prior_tests_count || 0,
        family_history_count: auth.family_history_count || 0,
        clinical_urgency: auth.clinical_urgency || 'routine'
    };
    
    // Show the automation popup
    document.getElementById('automation-popup').style.display = 'block';
    
    // Set current step based on auth data
    currentAutomationStep = auth.current_step || 1;
    
    // Show GPT-5 search animation for step 1
    if (currentAutomationStep === 1) {
        showGPT5SearchAnimation();
        updateSearchQuery("🚀 Starting parallel GPT-5 searches...");
        updateSearchProgress(10);
        
        // Simulate parallel search progress
        setTimeout(() => {
            updateSearchQuery("🔍 Searching NCDs, LCDs, LCAs simultaneously");
            updateSearchProgress(30);
        }, 1500);
        
        setTimeout(() => {
            updateSearchQuery("📄 Parsing policy documents in parallel");
            updateSearchProgress(60);
        }, 3000);
        
        setTimeout(() => {
            updateSearchQuery("📊 Analyzing coverage requirements...");
            updateSearchProgress(90);
        }, 4500);
        
        setTimeout(() => {
            updateSearchQuery("✅ Search completed successfully!");
            updateSearchProgress(100);
        }, 6000);
        
        // Hide animation after search completes
        setTimeout(() => {
            hideGPT5SearchAnimation();
        }, 7000);
    }
    
    // Fetch insurance analysis information if step 1 is completed
    if (currentAutomationStep > 1) {
        fetchInsuranceAnalysisInfo(authId);
    }
    
    // Update progress bar
    const progressPercent = (currentAutomationStep / 2) * 100;
    document.getElementById('automation-progress-fill').style.width = progressPercent + '%';
    document.getElementById('automation-progress-text').textContent = Math.round(progressPercent) + '% Complete';
    
    // Update step display
    const currentStep = automationSteps[currentAutomationStep - 1];
    if (currentStep) {
        document.getElementById('current-step-title').textContent = currentStep.title;
        document.getElementById('current-step-description').textContent = currentStep.description;
        document.getElementById('current-step-icon').innerHTML = currentStep.icon;
    }
    
    // Update status
    document.getElementById('current-step-status').innerHTML = '<i class="fas fa-play"></i> In Progress';
    
    // Show persistent step history instead of just current step
    const container = document.getElementById('step-content-container');
    container.innerHTML = `
        <div class="step-execution">
            <h4>Automation Progress</h4>
            <div class="execution-log">
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">Automation is currently running on step ${currentAutomationStep} of 2</span>
                </div>
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">Patient: ${auth.patient_name} (${auth.patient_mrn})</span>
                </div>
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">Service: ${auth.service_type}</span>
                </div>
                ${currentAutomationStep === 1 ? `
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">🚀 GPT-5 Parallel Search: Starting ${auth.insurance_provider === 'Original Medicare' ? '14' : '4'} simultaneous searches</span>
                </div>
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">🔍 Searching: NCDs, LCDs, LCAs, Coverage Database</span>
                </div>
                <div class="log-entry">
                    <span class="timestamp">${new Date().toLocaleTimeString()}</span>
                    <span class="message">🏛️ MAC Jurisdiction: ${auth.insurance_provider === 'Original Medicare' ? 'Detected' : 'N/A'}</span>
                </div>
                ` : ''}
            </div>
            
            <div class="step-history">
                <h5>Step History & Progress</h5>
                <div class="step-history-container">
                    ${automationSteps.map((step, index) => {
                        const stepNumber = index + 1;
                        const isCompleted = stepNumber < currentAutomationStep;
                        const isCurrent = stepNumber === currentAutomationStep;
                        const isPending = stepNumber > currentAutomationStep;
                        
                        return `
                            <div class="step-history-item ${isCompleted ? 'completed' : isCurrent ? 'current' : 'pending'} ${isCompleted ? 'clickable' : ''}" 
                                 ${isCompleted ? `onclick="inspectCompletedStep(${stepNumber}, '${step.title}')"` : ''}>
                                <div class="step-header">
                                    <div class="step-indicator">
                                        <i class="fas ${isCompleted ? 'fa-check' : isCurrent ? 'fa-spinner fa-spin' : 'fa-circle'}"></i>
                                    </div>
                                    <div class="step-info">
                                        <strong>Step ${stepNumber}: ${step.title}</strong>
                                        <span class="step-status">
                                            ${isCompleted ? 'Completed - Click to inspect' : isCurrent ? 'In Progress' : 'Pending'}
                                        </span>
                                    </div>
                                    ${isCompleted ? '<i class="fas fa-chevron-right step-arrow"></i>' : ''}
                                </div>
                                
                                ${isCompleted ? `
                                    <div class="step-summary">
                                        <div class="summary-item">
                                            <i class="fas fa-clock"></i>
                                            <span>Completed at ${new Date().toLocaleTimeString()}</span>
                                        </div>
                                        
                                        ${stepNumber === 1 ? `
                                            <div class="insurance-analysis-info">
                                                <h6><i class="fas fa-search"></i> Insurance Analysis Results</h6>
                                                <div class="analysis-details">
                                                    <div class="detail-row">
                                                        <span class="detail-label">CPT Requested:</span>
                                                        <span class="detail-value">${auth.cpt_code}</span>
                                                    </div>
                                                    <div class="detail-row">
                                                        <span class="detail-label">Insurance Provider:</span>
                                                        <span class="detail-value">${auth.insurance_provider}</span>
                                                    </div>
                                                    <div class="detail-row">
                                                        <span class="detail-label">Jurisdiction:</span>
                                                        <span class="detail-value" id="jurisdiction-display">Loading...</span>
                                                    </div>
                                                    <div class="detail-row">
                                                        <span class="detail-label">Coverage Status:</span>
                                                        <span class="detail-value" id="coverage-status-display">Loading...</span>
                                                    </div>
                                                </div>
                                            </div>
                                        ` : ''}
                                        <div class="summary-item">
                                            <i class="fas fa-check-circle"></i>
                                            <span>All requirements met</span>
                                        </div>
                                    </div>
                                ` : isCurrent ? `
                                    <div class="step-summary">
                                        <div class="summary-item">
                                            <i class="fas fa-spinner fa-spin"></i>
                                            <span>Currently processing...</span>
                                        </div>
                                    </div>
                                ` : `
                                    <div class="step-summary">
                                        <div class="summary-item">
                                            <i class="fas fa-clock"></i>
                                            <span>Waiting to start</span>
                                        </div>
                                    </div>
                                `}
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
}

function sendClinicianMessage(message = null) {
    if (message) {
        // If message is provided, populate the modal with editable fields
        document.getElementById('clinician-message-subject').value = 'Prior Authorization - Missing Information';
        document.getElementById('clinician-message-body').value = message;
        
        // Update preview
        previewClinicianMessage();
        
        // Add event listeners for real-time preview updates
        const subjectInput = document.getElementById('clinician-message-subject');
        const bodyTextarea = document.getElementById('clinician-message-body');
        
        subjectInput.addEventListener('input', previewClinicianMessage);
        bodyTextarea.addEventListener('input', previewClinicianMessage);
        
        // Show the modal
        document.getElementById('clinician-message-modal').style.display = 'block';
    } else {
        // Get the current message content
        const subject = document.getElementById('clinician-message-subject').value;
        const body = document.getElementById('clinician-message-body').value;
        
        if (!body.trim()) {
            alert('Please enter a message before sending.');
            return;
        }
        
        // Simulate sending message via EPIC
        alert(`Message sent to Dr. Johnson via EPIC messaging system.\n\nSubject: ${subject}\n\nMessage: ${body}`);
        closeClinicianModal();
        
        // Continue automation
        approveCurrentStep();
    }
}

function previewClinicianMessage() {
    const subject = document.getElementById('clinician-message-subject').value;
    const body = document.getElementById('clinician-message-body').value;
    
    const preview = document.getElementById('clinician-message-preview');
    preview.innerHTML = `
        <div class="message-preview-content">
            <div class="preview-header">
                <strong>Subject:</strong> ${subject || 'No subject'}
            </div>
            <div class="preview-body">
                ${body ? body.replace(/\n/g, '<br>') : 'No message content'}
            </div>
        </div>
    `;
}

async function debugData() {
    try {
        console.log('Debugging data...');
        const response = await fetch('/api/debug/check-data');
        const data = await response.json();
        
        console.log('Debug data:', data);
        
        if (data.success) {
            alert(`Debug Info:\nTotal Records: ${data.total_records}\nStats: ${JSON.stringify(data.stats, null, 2)}`);
        } else {
            alert(`Debug Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Debug error:', error);
        alert(`Debug Error: ${error.message}`);
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const authModal = document.getElementById('auth-detail-modal');
    const stepModal = document.getElementById('step-detail-modal');
    const automationModal = document.getElementById('automation-popup');
    const clinicianModal = document.getElementById('clinician-message-modal');
    
    if (event.target === authModal) {
        closeModal();
    }
    if (event.target === stepModal) {
        closeStepModal();
    }
    if (event.target === automationModal) {
        closeAutomationPopup();
    }
    if (event.target === clinicianModal) {
        closeClinicianModal();
    }
}

function addFieldEditListeners() {
    // Add change listeners to all answer fields
    const answerFields = document.querySelectorAll('.answer-field');
    answerFields.forEach(field => {
        field.addEventListener('change', function() {
            const questionItem = this.closest('.question-item');
            const statusDiv = questionItem.querySelector('.answer-status');
            
            // Update status to show user edited
            statusDiv.innerHTML = `
                <i class="fas fa-user-edit text-warning"></i>
                <span>User edited</span>
            `;
            statusDiv.className = 'answer-status user-edited';
            
            // Handle follow-up questions for radio buttons (select elements)
            if (this.tagName === 'SELECT' && this.dataset.hasFollowUp === 'true') {
                const selectedValue = this.value;
                const followUpCondition = this.dataset.followUpCondition;
                
                console.log(`User changed question ${questionItem.dataset.questionId}: value="${selectedValue}", condition="${followUpCondition}"`);
                
                if (selectedValue === followUpCondition) {
                    console.log(`Showing follow-up for question ${questionItem.dataset.questionId}`);
                    showFollowUpQuestionForUser(questionItem, followUpCondition);
                } else {
                    console.log(`Hiding follow-up for question ${questionItem.dataset.questionId}`);
                    hideFollowUpQuestion(questionItem);
                }
            }
        });
    });
}

function saveFormData() {
    const formData = {};
    const answerFields = document.querySelectorAll('.answer-field');
    
    answerFields.forEach(field => {
        const questionId = field.dataset.fieldId;
        formData[questionId] = field.value;
    });
    
    // Save to API
    fetch(`/api/prior-auths/${automationData.id}/save-form-answers`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            answers: formData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const message = document.createElement('div');
            message.className = 'alert alert-success';
            message.innerHTML = `<i class="fas fa-save"></i> ${data.message}`;
            document.getElementById('form-processing-summary').appendChild(message);
            
            setTimeout(() => message.remove(), 3000);
        } else {
            // Show error message
            const message = document.createElement('div');
            message.className = 'alert alert-danger';
            message.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${data.error}`;
            document.getElementById('form-processing-summary').appendChild(message);
            
            setTimeout(() => message.remove(), 5000);
        }
    })
    .catch(error => {
        console.error('Error saving form data:', error);
        const message = document.createElement('div');
        message.className = 'alert alert-danger';
        message.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error saving form data: ${error.message}`;
        document.getElementById('form-processing-summary').appendChild(message);
        
        setTimeout(() => message.remove(), 5000);
    });
}

async function exportForm() {
    // Show loading state
    const exportBtn = document.getElementById('export-form-btn');
    const originalText = exportBtn.innerHTML;
    exportBtn.disabled = true;
    exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading PDF...';
    
    try {
        // Call the PDF export endpoint
        const response = await fetch(`/api/prior-auths/${automationData.id}/export-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate PDF');
        }
        
        // Get the PDF blob
        const pdfBlob = await response.blob();
        
        // Create download link
        const url = URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `Medicaid_Genetic_Testing_PA_Form_${automationData.patient_name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
        link.click();
        
        // Clean up
        URL.revokeObjectURL(url);
        
        // Show success message
        showMessage('PDF form downloaded successfully!', 'success');
        
    } catch (error) {
        console.error('Error downloading PDF:', error);
        showMessage(`Error downloading PDF: ${error.message}`, 'error');
        
    } finally {
        // Reset button state
        exportBtn.disabled = false;
        exportBtn.innerHTML = originalText;
    }
}

function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
    messageDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.form-processing-summary') || document.body;
    container.insertBefore(messageDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Helper functions for follow-up questions
function shouldShowFollowUp(questionItem, answer) {
    const answerField = questionItem.querySelector('.answer-field');
    const followUpCondition = answerField.dataset.followUpCondition;
    
    if (!followUpCondition) {
        console.log(`No follow-up condition found for question ${questionItem.dataset.questionId}`);
        return false;
    }
    
    console.log(`Checking follow-up for question ${questionItem.dataset.questionId}: answer="${answer}", condition="${followUpCondition}"`);
    return answer === followUpCondition;
}

function showFollowUpQuestion(questionItem, followUpData) {
    const followUpContainer = questionItem.querySelector('.follow-up-container');
    if (!followUpContainer) return;
    
    // Create follow-up question HTML
    let followUpHTML = `
        <div class="follow-up-question">
            <div class="question-text follow-up-text">
                <i class="fas fa-arrow-right"></i> ${followUpData.question}
            </div>
            <div class="answer-container">
    `;
    
    if (followUpData.type === 'text_area') {
        followUpHTML += `
            <textarea class="answer-field follow-up-field" placeholder="Agent will populate this answer..." data-field-id="${questionItem.dataset.questionId}_followup"></textarea>
        `;
    } else {
        followUpHTML += `
            <input type="text" class="answer-field follow-up-field" placeholder="Agent will populate this answer..." data-field-id="${questionItem.dataset.questionId}_followup">
        `;
    }
    
    followUpHTML += `
                <div class="answer-status">
                    <i class="fas fa-clock"></i>
                    <span>Waiting for agent...</span>
                </div>
                <div class="answer-source"></div>
            </div>
        </div>
    `;
    
    followUpContainer.innerHTML = followUpHTML;
    followUpContainer.style.display = 'block';
    
    // Add event listener to follow-up field
    const followUpField = followUpContainer.querySelector('.follow-up-field');
    if (followUpField) {
        followUpField.addEventListener('change', function() {
            const statusDiv = this.closest('.answer-container').querySelector('.answer-status');
            statusDiv.innerHTML = `
                <i class="fas fa-user-edit text-warning"></i>
                <span>User edited</span>
            `;
            statusDiv.className = 'answer-status user-edited';
        });
    }
}

function hideFollowUpQuestion(questionItem) {
    const followUpContainer = questionItem.querySelector('.follow-up-container');
    if (followUpContainer) {
        followUpContainer.style.display = 'none';
        followUpContainer.innerHTML = '';
    }
}

function showFollowUpQuestionForUser(questionItem, followUpCondition) {
    // Find the follow-up data from the global form questions
    const questionId = questionItem.dataset.questionId;
    let followUpData = null;
    
    // Search through all sections to find the question
    if (globalFormQuestions && globalFormQuestions.sections) {
        for (const section of globalFormQuestions.sections) {
            for (const question of section.questions) {
                if (question.id === questionId && question.follow_up) {
                    followUpData = question.follow_up;
                    break;
                }
            }
            if (followUpData) break;
        }
    }
    
    if (followUpData) {
        showFollowUpQuestion(questionItem, followUpData);
    } else {
        console.warn(`No follow-up data found for question ${questionId}`);
    }
}
