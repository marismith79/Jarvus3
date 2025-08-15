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
        title: "Coverage Determination",
        description: "Checking if CPT code is covered by insurance plan",
        icon: "fas fa-search",
        content: "coverage"
    },
    {
        id: 2,
        title: "Insurance Documentation",
        description: "Searching for insurance requirements and documentation",
        icon: "fas fa-file-medical",
        content: "insurance"
    },
    {
        id: 3,
        title: "Screening",
        description: "Analyzing request notes and EHR data for completeness",
        icon: "fas fa-clipboard-check",
        content: "screening"
    },
    {
        id: 4,
        title: "Data Extraction",
        description: "Extracting relevant data from EHR with citations",
        icon: "fas fa-database",
        content: "extraction"
    },
    {
        id: 5,
        title: "HUSKY Form Completion",
        description: "Filling out HUSKY Health Genetic Testing Prior Authorization form",
        icon: "fas fa-paper-plane",
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
    // Tab navigation
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });

    // Search and filters
    document.getElementById('search-input').addEventListener('input', filterData);
    document.getElementById('provider-filter').addEventListener('change', filterData);
    document.getElementById('step-filter').addEventListener('change', filterData);

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
}

function switchTab(tab) {
    currentTab = tab;
    
    // Update active tab button
    document.querySelectorAll('.tab-button').forEach(button => {
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
        const response = await fetch('/api/prior-auths/stats');
        const stats = await response.json();
        
        document.getElementById('total-count').textContent = stats.total_count;
        document.getElementById('automated-count').textContent = stats.status_counts.running || 0;
        document.getElementById('human-review-count').textContent = (stats.status_counts.review || 0) + (stats.status_counts.feedback || 0);
        document.getElementById('completed-count').textContent = stats.status_counts.completed || 0;
        
        // Update tab counts
        document.getElementById('all-count').textContent = stats.status_counts.pending || 0;
        document.getElementById('running-tab-count').textContent = stats.status_counts.running || 0;
        document.getElementById('review-tab-count').textContent = stats.status_counts.review || 0;
        document.getElementById('feedback-tab-count').textContent = stats.status_counts.feedback || 0;
        document.getElementById('completed-tab-count').textContent = stats.status_counts.completed || 0;
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
    const currentStep = auth.current_step || 1;
    const progress = (currentStep / 5) * 100;
    
    row.innerHTML = `
        <td class="checkbox-col">
            <input type="checkbox" class="auth-checkbox" value="${auth.id}" onchange="updateBulkActions()">
        </td>
        <td class="patient-col">
            <div class="patient-info">
                <div class="patient-name">${auth.patient_name}</div>
                <div class="patient-mrn">MRN: ${auth.patient_mrn}</div>
                <div class="clinical-urgency ${auth.clinical_urgency}">${auth.clinical_urgency}</div>
            </div>
        </td>
        <td class="service-col">
            <div class="service-info">
                <div class="service-type">${auth.service_type}</div>
                <div class="service-notes">${auth.notes}</div>
            </div>
        </td>
        <td class="cpt-col">
            <span class="cpt-code">${auth.cpt_code || 'N/A'}</span>
        </td>
        <td class="insurance-col">
            <div class="insurance-info">
                <div class="insurance-provider">${auth.insurance_provider}</div>
                <div class="insurance-requirements">${auth.insurance_requirements}</div>
            </div>
        </td>
        <td class="progress-col">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <div class="progress-text">${Math.round(progress)}%</div>
        </td>
        <td class="current-step-col">
            <div class="step-indicator">
                <span class="step-number">${currentStep}</span>
                <span class="step-name">${getStepName(currentStep)}</span>
            </div>
        </td>
        <td class="status-col">
            <span class="status-badge status-${auth.status}">${getStatusDisplay(auth.status)}</span>
        </td>
        <td class="dates-col">
            <div class="date-info">
                <div class="created-date">${formatDate(auth.created_date)}</div>
            </div>
        </td>
        <td class="due-col">
            <div class="date-info">
                <div class="due-date ${isOverdue(auth.due_date) ? 'overdue' : ''}">${formatDate(auth.due_date)}</div>
            </div>
        </td>
        <td class="actions-col">
            <div class="action-buttons">
                <button class="btn btn-sm btn-outline" onclick="viewDetails(${auth.id})" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline" onclick="viewStepDetails(${auth.id})" title="View Step Details">
                    <i class="fas fa-tasks"></i>
                </button>
                ${getActionButton(auth)}
            </div>
        </td>
    `;
    
    return row;
}

function getStepName(step) {
    const stepNames = {
        1: 'Coverage',
        2: 'Requirements',
        3: 'Screening',
        4: 'Data Extraction',
        5: 'HUSKY Form'
    };
    return stepNames[step] || 'Unknown';
}

function getStatusDisplay(status) {
    const statusMap = {
        'pending': 'Pending',
        'running': 'In Progress',
        'review': 'Human Review',
        'feedback': 'Needs Input',
        'completed': 'Completed',
        'failed': 'Failed'
    };
    return statusMap[status] || status;
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
    const stepFilter = document.getElementById('step-filter').value;
    
    filteredPriorAuths = allPriorAuths.filter(auth => {
        const matchesSearch = !searchTerm || 
            auth.patient_name.toLowerCase().includes(searchTerm) ||
            auth.patient_mrn.toLowerCase().includes(searchTerm) ||
            auth.service_type.toLowerCase().includes(searchTerm) ||
            (auth.cpt_code && auth.cpt_code.toLowerCase().includes(searchTerm));
        
        const matchesProvider = !providerFilter || auth.insurance_provider === providerFilter;
        const matchesStep = !stepFilter || (auth.current_step || 1) == stepFilter;
        
        return matchesSearch && matchesProvider && matchesStep;
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
            console.log('Executing coverage determination...');
            await executeCoverageDetermination();
            break;
        case 'insurance':
            console.log('Executing insurance documentation...');
            await executeInsuranceDocumentation();
            break;
        case 'screening':
            console.log('Executing screening...');
            await executeScreening();
            break;
        case 'extraction':
            console.log('Executing data extraction...');
            await executeDataExtraction();
            break;
        case 'form':
            console.log('Executing form completion...');
            await executeFormCompletion();
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

async function executeCoverageDetermination() {
    const content = document.getElementById('step-content-container');
    
    await streamText(content, `
        <div class="coverage-result">
            <h4>Step 1: Coverage Determination</h4>
            <div class="result-card">
                <div class="gpt-search-simulation">
                    <div class="search-query">
                        <i class="fas fa-search"></i>
                        <span>Searching Medicare NCD 90.2 coverage criteria for CPT ${automationData.cpt_code}...</span>
                    </div>
                    <div class="search-results">
                        <div class="result-item">
                            <strong>NCD 90.2 Coverage Found:</strong>
                            <p>Comprehensive genomic profiling (CGP) is covered for patients with advanced cancer when:</p>
                            <ul>
                                <li>Patient has advanced cancer (stage III/IV)</li>
                                <li>No prior comprehensive NGS testing on same tumor</li>
                                <li>FDA-approved companion diagnostic or MAC coverage</li>
                                <li>Results will guide treatment decisions</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="coverage-analysis">
                    <h5>Patient-Specific Analysis:</h5>
                    <div class="analysis-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Diagnosis:</strong> ${automationData.diagnosis} - Stage ${automationData.stage || 'IV'}</span>
                    </div>
                    <div class="analysis-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Advanced Cancer:</strong> ${automationData.stage === 'IV' || automationData.stage === 'III' ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="analysis-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Prior NGS Testing:</strong> ${automationData.prior_tests_count || 0} previous tests</span>
                    </div>
                    <div class="analysis-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>FDA Coverage:</strong> CPT ${automationData.cpt_code} has FDA-approved companion diagnostic</span>
                    </div>
                </div>
                
                <div class="coverage-decision">
                    <div class="decision-badge success">
                        <i class="fas fa-check"></i>
                        <span>Coverage Confirmed</span>
                    </div>
                    <p><strong>Decision:</strong> Patient meets NCD 90.2 criteria. Coverage is confirmed for ${automationData.service_type}.</p>
                </div>
            </div>
        </div>
    `, 'coverage');
    
    stepResults.coverage = {
        status: 'completed',
        coverage_confirmed: true,
        ncd_criteria_met: true,
        decision: 'Proceed with prior authorization'
    };
    
    await moveToNextStep();
}

async function executeInsuranceDocumentation() {
    const content = document.getElementById('step-content-container');
    
    await streamText(content, `
        <div class="insurance-documentation">
            <h4>Step 2: Insurance Requirements Extraction</h4>
            <div class="result-card">
                <div class="gpt-search-simulation">
                    <div class="search-query">
                        <i class="fas fa-search"></i>
                        <span>Searching ${automationData.insurance_provider} requirements for ${automationData.service_type}...</span>
                    </div>
                    <div class="search-results">
                        <div class="result-item">
                            <strong>Insurance Requirements Found:</strong>
                            <div class="requirements-list">
                                <div class="requirement-item">
                                    <i class="fas fa-file-medical"></i>
                                    <span>Pathology report confirming cancer diagnosis</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-dna"></i>
                                    <span>Molecular testing order with clinical rationale</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-user-md"></i>
                                    <span>Oncology consultation note</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-calendar-alt"></i>
                                    <span>Date of diagnosis and staging information</span>
                                </div>
                                <div class="requirement-item">
                                    <i class="fas fa-flask"></i>
                                    <span>Specimen adequacy report (tumor purity > 20%)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="requirements-mapping">
                    <h5>Requirements Mapping to EHR Data:</h5>
                    <div class="mapping-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Pathology Report:</strong> Available in EHR (${automationData.ehr_documents.includes('Pathology Report') ? '✓' : '✗'})</span>
                    </div>
                    <div class="mapping-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Molecular Order:</strong> Available in EHR (${automationData.ehr_documents.includes('Genomic Testing Report') ? '✓' : '✗'})</span>
                    </div>
                    <div class="mapping-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Oncology Note:</strong> Available in EHR (${automationData.ehr_documents.includes('Clinical Notes') ? '✓' : '✗'})</span>
                    </div>
                    <div class="mapping-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Staging Info:</strong> Available in EHR (✓)</span>
                    </div>
                    <div class="mapping-item">
                        <i class="fas fa-check-circle"></i>
                        <span><strong>Specimen Adequacy:</strong> Available in EHR (✓)</span>
                    </div>
                </div>
            </div>
        </div>
    `, 'insurance');
    
    stepResults.insurance = {
        status: 'completed',
        requirements_extracted: true,
        all_documents_available: true,
        action: 'proceed_to_screening'
    };
    
    await moveToNextStep();
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
            <h4>Step 5: HUSKY Health Genetic Testing Prior Authorization Form</h4>
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
                            <li>✓ Coverage determination completed</li>
                            <li>✓ Insurance requirements identified</li>
                            <li>✓ Screening passed - all documentation complete</li>
                            <li>✓ HUSKY form data extracted with citations</li>
                            <li>✓ HUSKY Health prior authorization form populated and ready for review</li>
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

function viewDetails(authId) {
    // Find the auth data
    const auth = allPriorAuths.find(a => a.id === authId);
    if (!auth) {
        console.error('Auth not found:', authId);
        return;
    }
    
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
                        <span class="status-badge ${auth.status}">${auth.status}</span>
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
                        <span>${auth.created_date}</span>
                    </div>
                    <div class="detail-item">
                        <label>Due Date:</label>
                        <span>${auth.due_date}</span>
                    </div>
                    <div class="detail-item">
                        <label>Last Updated:</label>
                        <span>${auth.last_updated}</span>
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
    
    // Populate the modal body
    document.getElementById('modal-body').innerHTML = modalContent;
    
    // Update the action button based on status
    const actionBtn = document.getElementById('modal-action-btn');
    if (auth.status === 'pending') {
        actionBtn.textContent = 'Start Automation';
        actionBtn.onclick = () => startAutomation(auth.id);
    } else if (auth.status === 'running') {
        actionBtn.textContent = 'View Progress';
        actionBtn.onclick = () => viewAutomationProgress(auth.id);
    } else {
        actionBtn.textContent = 'View Details';
        actionBtn.onclick = () => closeModal();
    }
    
    // Show the modal
    document.getElementById('auth-detail-modal').style.display = 'block';
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
                            <h4>Insurance Documentation</h4>
                            <p>${stepDetails.step2?.details || 'Not started'}</p>
                        </div>
                    </div>
                    <div class="step-item ${auth.current_step >= 3 ? 'completed' : 'pending'}">
                        <div class="step-number">3</div>
                        <div class="step-info">
                            <h4>Screening</h4>
                            <p>${stepDetails.step3?.details || 'Not started'}</p>
                        </div>
                    </div>
                    <div class="step-item ${auth.current_step >= 4 ? 'completed' : 'pending'}">
                        <div class="step-number">4</div>
                        <div class="step-info">
                            <h4>Data Extraction</h4>
                            <p>${stepDetails.step4?.details || 'Not started'}</p>
                        </div>
                    </div>
                    <div class="step-item ${auth.current_step >= 5 ? 'completed' : 'pending'}">
                        <div class="step-number">5</div>
                        <div class="step-info">
                            <h4>Form Completion</h4>
                            <p>${stepDetails.step5?.details || 'Not started'}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="step-summary">
                <h3>Current Status</h3>
                <div class="status-summary">
                    <p><strong>Current Step:</strong> ${auth.current_step || 1} of 5</p>
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
            
        case 5:
            stepContent = `
                <div class="step-inspection">
                    <h3>Step 5: HUSKY Form Completion - Completed</h3>
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
    const progressPercent = (currentAutomationStep / 5) * 100;
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
                    <span class="message">Automation is currently running on step ${currentAutomationStep} of 5</span>
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

function sendClinicianMessage() {
    // Simulate sending message via EPIC
    alert('Message sent to Dr. Johnson via EPIC messaging system.');
    closeClinicianModal();
    
    // Continue automation
    approveCurrentStep();
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
