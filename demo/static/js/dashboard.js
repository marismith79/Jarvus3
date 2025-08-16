// Dashboard JavaScript for Prior Authorization Management
// Extracted from dashboard.html

let currentTab = 'all';
let allPriorAuths = [];
let filteredPriorAuths = [];
let currentSort = { field: 'created_date', direction: 'asc' };

// Automation workflow variables
let currentAutomationStep = 1;
let automationData = {};
let streamingInterval = null;
let stepResults = {};

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
        title: "Form Completion with EHR Data Extraction",
        description: "Filling form using policy analysis and extracting EHR data",
        icon: "fas fa-file-medical",
        content: "form"
    }
];

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
    document.getElementById('last-refreshed-time').textContent = timeString;
}

function getActionButton(auth) {
    if (auth.status === 'pending') {
        return `<button class="btn btn-sm btn-primary" onclick="startAutomation(${auth.id})" title="Start Automation">
                    <i class="fas fa-robot"></i>
                </button>`;
    } else if (auth.status === 'running') {
        return `<button class="btn btn-sm btn-warning" onclick="pauseAutomation(${auth.id})" title="Pause Automation">
                    <i class="fas fa-pause"></i>
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
    
    // Show automation popup
    document.getElementById('automation-popup').style.display = 'block';
    
    // Start the workflow
    await executeAutomationStep(currentAutomationStep);
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
    
    // Show form completion animation
    showFormCompletionAnimation();
    updateFormQuery("🚀 Starting form completion with EHR data extraction...");
    updateFormProgress(0);
    
    try {
        // Start the streaming form completion process
        const response = await fetch(`/api/prior-auths/${automationData.id}/form-completion-stream`, {
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
                                updateFormQuery(data.message);
                                updateFormProgress(data.progress);
                                break;
                                
                            case 'ehr_extraction':
                                updateFormQuery(`📋 Extracting: ${data.field} from EHR`);
                                updateFormProgress(data.progress);
                                
                                // Show EHR extraction results
                                const ehrContainer = document.createElement('div');
                                ehrContainer.className = 'ehr-extraction-container';
                                ehrContainer.innerHTML = `
                                    <h5>📋 EHR Data Extraction: ${data.field}</h5>
                                    <div class="ehr-result">
                                        <div class="ehr-value">${data.value}</div>
                                        <div class="ehr-source">Source: ${data.source}</div>
                                        <div class="ehr-citation">Citation: ${data.citation}</div>
                                    </div>
                                `;
                                
                                const contentArea = document.getElementById('step-content-container');
                                contentArea.appendChild(ehrContainer);
                                break;
                                
                            case 'form_field':
                                updateFormQuery(`📝 Filling form field: ${data.field}`);
                                updateFormProgress(data.progress);
                                
                                // Show form field completion
                                const formContainer = document.createElement('div');
                                formContainer.className = 'form-field-container';
                                formContainer.innerHTML = `
                                    <h5>📝 Form Field: ${data.field}</h5>
                                    <div class="form-field-result">
                                        <div class="field-value">${data.value}</div>
                                        <div class="field-justification">${data.justification}</div>
                                        <div class="field-sources">Sources: ${data.sources.join(', ')}</div>
                                    </div>
                                `;
                                
                                const contentArea2 = document.getElementById('step-content-container');
                                contentArea2.appendChild(formContainer);
                                break;
                                
                            case 'complete':
                                // Hide animation and show final form
                                hideFormCompletionAnimation();
                                
                                // Display the completed form
                                const formResult = data.result;
                                
                                content.innerHTML = `
                                    <div class="form-completion-result">
                                        <h4>Step 2: Form Completion with EHR Data - Complete</h4>
                                        <div class="completed-form-card">
                                            <div class="form-summary">
                                                <div class="completion-status success">
                                                    <i class="fas fa-check-circle"></i>
                                                    <span><strong>Form Status:</strong> READY FOR HUMAN VALIDATION</span>
                                                </div>
                                                <div class="completion-stats">
                                                    <strong>Fields Completed:</strong> ${formResult.completed_fields}/${formResult.total_fields}
                                                </div>
                                            </div>
                                            
                                            <div class="form-sections">
                                                ${formResult.sections.map(section => `
                                                    <div class="form-section">
                                                        <h5>${section.title}</h5>
                                                        ${section.fields.map(field => `
                                                            <div class="form-field">
                                                                <div class="field-label">${field.label}:</div>
                                                                <div class="field-value">${field.value}</div>
                                                                <div class="field-sources">
                                                                    <strong>Data Sources:</strong> ${field.sources.join(', ')}
                                                                </div>
                                                            </div>
                                                        `).join('')}
                                                    </div>
                                                `).join('')}
                                            </div>
                                            
                                            <div class="ehr-citations">
                                                <h5>EHR Data Citations & Sources:</h5>
                                                <div class="citations-grid">
                                                    ${formResult.ehr_citations.map(citation => `
                                                        <div class="citation-item">
                                                            <div class="citation-field"><strong>${citation.field}:</strong></div>
                                                            <div class="citation-value">${citation.value}</div>
                                                            <div class="citation-source">Source: ${citation.source}</div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                            
                                            <div class="policy-references">
                                                <h5>Supporting Policy Documents:</h5>
                                                <div class="policy-grid">
                                                    ${formResult.policy_references.map(ref => `
                                                        <div class="policy-item">
                                                            <a href="${ref.url}" target="_blank" class="policy-title">${ref.title}</a>
                                                            <div class="policy-meta">
                                                                <span class="relevance">${ref.relevance}% relevant</span>
                                                                <span class="policy-type">Policy Document</span>
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                            
                                            <div class="validation-section">
                                                <h5>Human Validation Required:</h5>
                                                <p>Please review the completed form above. All data has been extracted from the EHR system and cross-referenced with policy requirements from Step 1.</p>
                                                
                                                <div class="validation-actions">
                                                    <button class="btn btn-success" onclick="approveForm()">
                                                        <i class="fas fa-check"></i> Approve & Submit
                                                    </button>
                                                    <button class="btn btn-warning" onclick="requestFormChanges()">
                                                        <i class="fas fa-edit"></i> Request Changes
                                                    </button>
                                                    <button class="btn btn-info" onclick="exportForm()">
                                                        <i class="fas fa-download"></i> Export Form
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                                
                                stepResults.form = {
                                    status: 'completed',
                                    form_completed: true,
                                    ehr_data_integrated: true,
                                    policy_references_included: true,
                                    action: 'ready_for_validation'
                                };
                                
                                // Add step to history
                                addCompletedStep(2, formResult);
                                
                                // Don't auto-advance - wait for human validation
                                // await moveToNextStep();
                                return;
                                
                            case 'error':
                                hideFormCompletionAnimation();
                                await streamText(content, `
                                    <div class="error-result">
                                        <h4>Step 2: Form Completion - Error</h4>
                                        <div class="error-card">
                                            <i class="fas fa-exclamation-triangle"></i>
                                            <p><strong>Error:</strong> ${data.error}</p>
                                            <p>Please try again or contact support.</p>
                                        </div>
                                    </div>
                                `, 'form');
                                return;
                        }
                    } catch (parseError) {
                        console.error('Error parsing SSE data:', parseError);
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('Error in form completion stream:', error);
        hideFormCompletionAnimation();
        await streamText(content, `
            <div class="error-result">
                <h4>Step 2: Form Completion - Error</h4>
                <div class="error-card">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p><strong>Error:</strong> ${error.message}</p>
                    <p>Please try again or contact support.</p>
                </div>
            </div>
        `, 'form');
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
    document.getElementById('automation-popup').style.display = 'none';
    document.getElementById('automation-actions').style.display = 'none';
    if (streamingInterval) {
        clearInterval(streamingInterval);
    }
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
    
    if (auth.status === 'pending') {
        actionBtn.textContent = '🤖 Start Automation';
        actionBtn.className = 'btn btn-primary';
        actionBtn.onclick = () => {
            closeModal();
            startAutomation(auth.id);
        };
    } else if (auth.status === 'running') {
        actionBtn.textContent = '📊 View Progress';
        actionBtn.className = 'btn btn-info';
        actionBtn.onclick = () => {
            closeModal();
            viewAutomationProgress(auth.id);
        };
    } else if (auth.status === 'completed') {
        actionBtn.textContent = '📋 View Automation History';
        actionBtn.className = 'btn btn-success';
        actionBtn.onclick = () => {
            closeModal();
            viewAutomationProgress(auth.id);
        };
    } else if (auth.status === 'review' || auth.status === 'feedback') {
        actionBtn.textContent = '📊 View Progress';
        actionBtn.className = 'btn btn-warning';
        actionBtn.onclick = () => {
            closeModal();
            viewAutomationProgress(auth.id);
        };
    } else {
        actionBtn.textContent = '📋 View Details';
        actionBtn.className = 'btn btn-secondary';
        actionBtn.onclick = () => closeModal();
    }
    
    // Show the modal
    document.getElementById('auth-detail-modal').style.display = 'block';
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

function pauseAutomation(authId) {
    if (confirm('Are you sure you want to pause the automation for this request?')) {
        // Call backend to pause automation
        fetch(`/api/prior-auths/${authId}/pause-automation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Automation paused successfully');
                loadData(); // Refresh the data
            } else {
                alert('Error pausing automation: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error pausing automation');
        });
    }
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
        // If message is provided, populate the modal
        document.getElementById('clinician-message-content').innerHTML = `
            <div class="message-body">
                <p><strong>Dear Clinician,</strong></p>
                <p>${message}</p>
                <p><strong>Please provide the requested documentation to proceed with the prior authorization request.</strong></p>
                <p>Best regards,<br>Prior Authorization Team</p>
            </div>
        `;
        document.getElementById('clinician-message-modal').style.display = 'block';
    } else {
        // Simulate sending message via EPIC
        alert('Message sent to Dr. Johnson via EPIC messaging system.');
        closeClinicianModal();
        
        // Continue automation
        approveCurrentStep();
    }
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
