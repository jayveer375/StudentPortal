// =========================================================
// EXAMDESK - PROFESSIONAL SAAS CONTROLLER
// Left Sidebar Navigation, Breadcrumb Management, View Router,
// Data Persistence, Live Roster Search/Filter, CSV Export & Copy
// =========================================================

// Global state
let matchedStudents = [];
let notFoundStudentsList = [];
let invalidStudentsList = [];
let currentUploadToken = null;
let currentMessageSession = null;
let currentMessageType = null;
let currentFilteredStudents = [];

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const pdfFileInput = document.getElementById('pdfFile');
const fileLabelText = document.querySelector('.file-label-text');
const uploadStatus = document.getElementById('uploadStatus');
const resultsSection = document.getElementById('resultsSection');
const rosterEmptyState = document.getElementById('rosterEmptyState');
const sendEmailsBtn = document.getElementById('sendEmailsBtn');
const cancelBtn = document.getElementById('cancelBtn');
const messageStatus = document.getElementById('messageStatus');
const progressSection = document.getElementById('progressSection');
const progressTitle = document.getElementById('progressTitle');
const dropzoneArea = document.getElementById('dropzoneArea');
const currentBreadcrumb = document.getElementById('currentBreadcrumb');

// Quick jump banner
const quickJumpBanner = document.getElementById('quickJumpBanner');
const quickJumpTitle = document.getElementById('quickJumpTitle');
const quickJumpDesc = document.getElementById('quickJumpDesc');
const jumpToRosterBtn = document.getElementById('jumpToRosterBtn');
const jumpToDispatchBtn = document.getElementById('jumpToDispatchBtn');
const emptyStateUploadBtn = document.getElementById('emptyStateUploadBtn');
const topbarUploadBtn = document.getElementById('topbarUploadBtn');
const appSidebar = document.getElementById('appSidebar');
const mobileNavToggle = document.getElementById('mobileNavToggle');
const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');

// Badges
const rosterBadge = document.getElementById('rosterBadge');
const auditBadge = document.getElementById('auditBadge');
const notFoundCountBadge = document.getElementById('notFoundCountBadge');
const invalidEmailCountBadge = document.getElementById('invalidEmailCountBadge');
const auditCleanState = document.getElementById('auditCleanState');
const auditEmptyPrompt = document.getElementById('auditEmptyPrompt');

// Search & Filter
const rosterSearchInput = document.getElementById('rosterSearchInput');
const rosterSemFilter = document.getElementById('rosterSemFilter');
const rosterFilterCount = document.getElementById('rosterFilterCount');
const copyRosterBtn = document.getElementById('copyRosterBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const copyNotFoundBtn = document.getElementById('copyNotFoundBtn');

// View Names Mapping for Breadcrumbs
const viewTitleMap = {
    'view-upload': 'Upload File',
    'view-arrangements': 'Manage Seating',
    'view-roster': 'Students',
    'view-audit': 'Issues',
    'view-dispatch': 'Send Notifications',
    'view-guide': 'Guidelines & Schema'
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupSidebarNavigation();
    setupEventListeners();
    setupDropzone();
    setupRosterSearchFilter();
    setupExportUtilities();
    restoreSessionData();
    loadArrangements();
});

// =========================================================
// SIDEBAR & VIEW ROUTING
// =========================================================
function setupSidebarNavigation() {
    const navItems = document.querySelectorAll('.sidebar .nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetView = this.getAttribute('data-view');
            switchView(targetView);
            closeMobileSidebar();
        });
    });

    // Mobile navigation drawer toggle controls
    if (mobileNavToggle) {
        mobileNavToggle.addEventListener('click', toggleMobileSidebar);
    }
    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener('click', closeMobileSidebar);
    }
    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', closeMobileSidebar);
    }

    // Close mobile drawer on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMobileSidebar();
        }
    });

    // Auto-close mobile drawer when window resized past tablet breakpoint (> 1024px)
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1024) {
            closeMobileSidebar();
        }
    });

    // Sidebar collapse toggle — arrow button at bottom of sidebar footer (desktop mode)
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const mainViewport       = document.querySelector('.main-viewport');

    if (sidebarCollapseBtn && appSidebar && mainViewport) {
        sidebarCollapseBtn.addEventListener('click', () => {
            const isCollapsed = appSidebar.classList.toggle('collapsed');
            mainViewport.classList.toggle('sidebar-collapsed', isCollapsed);
        });
    }

    // Direct link buttons
    if (jumpToRosterBtn) jumpToRosterBtn.addEventListener('click', () => switchView('view-roster'));
    if (jumpToDispatchBtn) jumpToDispatchBtn.addEventListener('click', () => switchView('view-dispatch'));
    if (emptyStateUploadBtn) emptyStateUploadBtn.addEventListener('click', () => switchView('view-upload'));
    if (topbarUploadBtn) topbarUploadBtn.addEventListener('click', () => switchView('view-upload'));

    // Handle hash in URL
    const hash = window.location.hash.replace('#', '');
    if (hash && document.getElementById(hash)) {
        switchView(hash);
    }
}

function switchView(viewId) {
    if (!viewId || !document.getElementById(viewId)) return;

    // Update sidebar active classes
    document.querySelectorAll('.sidebar .nav-item').forEach(item => {
        if (item.getAttribute('data-view') === viewId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update view sections
    document.querySelectorAll('.view-section').forEach(view => {
        if (view.id === viewId) {
            view.classList.add('active');
        } else {
            view.classList.remove('active');
        }
    });

    // Update breadcrumb
    if (currentBreadcrumb && viewTitleMap[viewId]) {
        currentBreadcrumb.textContent = viewTitleMap[viewId];
    }

    // Update URL hash
    history.replaceState(null, null, `#${viewId}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (viewId === 'view-arrangements') {
        loadArrangements();
    }
}

// Mobile sidebar drawer helper functions
function openMobileSidebar() {
    if (appSidebar) appSidebar.classList.add('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
    document.body.classList.add('drawer-open');
}

function closeMobileSidebar() {
    if (appSidebar) appSidebar.classList.remove('open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
    document.body.classList.remove('drawer-open');
}

function toggleMobileSidebar() {
    if (appSidebar && appSidebar.classList.contains('open')) {
        closeMobileSidebar();
    } else {
        openMobileSidebar();
    }
}

// =========================================================
// EVENT LISTENERS
// =========================================================
function setupEventListeners() {
    // File input change
    pdfFileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const fileName = this.files[0].name;
            const fileSize = formatFileSize(this.files[0].size);
            if (fileLabelText) fileLabelText.textContent = `${fileName} (${fileSize})`;
        } else {
            if (fileLabelText) fileLabelText.textContent = 'Choose PDF or Excel File (.pdf, .xlsx, .xls)';
        }
    });

    // Form submit
    uploadForm.addEventListener('submit', handleFileUpload);

    // Send emails
    sendEmailsBtn.addEventListener('click', handleSendEmails);

    // Cancel
    cancelBtn.addEventListener('click', handleCancel);

    // Arrangements buttons
    const jumpToArrangementsBtn = document.getElementById('jumpToArrangementsBtn');
    if (jumpToArrangementsBtn) {
        jumpToArrangementsBtn.addEventListener('click', () => switchView('view-arrangements'));
    }
    const refreshArrangementsBtn = document.getElementById('refreshArrangementsBtn');
    if (refreshArrangementsBtn) {
        refreshArrangementsBtn.addEventListener('click', () => loadArrangements());
    }
    const newArrangementUploadBtn = document.getElementById('newArrangementUploadBtn');
    if (newArrangementUploadBtn) {
        newArrangementUploadBtn.addEventListener('click', () => switchView('view-upload'));
    }
    const emptyArrangementsUploadBtn = document.getElementById('emptyArrangementsUploadBtn');
    if (emptyArrangementsUploadBtn) {
        emptyArrangementsUploadBtn.addEventListener('click', () => switchView('view-upload'));
    }
}

// =========================================================
// DRAG & DROP
// =========================================================
function setupDropzone() {
    if (!dropzoneArea) return;

    dropzoneArea.addEventListener('click', () => {
        pdfFileInput.click();
    });

    ['dragenter', 'dragover'].forEach(name => {
        dropzoneArea.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropzoneArea.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzoneArea.classList.remove('drag-over');
        });
    });

    dropzoneArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
            pdfFileInput.files = dt.files;
            pdfFileInput.dispatchEvent(new Event('change'));
        }
    });
}

// =========================================================
// UPLOAD & PARSING HANDLER
// =========================================================
async function handleFileUpload(event) {
    event.preventDefault();
    
    const file = pdfFileInput.files[0];
    if (!file) {
        showStatus(uploadStatus, '⚠️ Please select a PDF or Excel file first.', 'error');
        return;
    }

    const validationError = validateFile(file);
    if (validationError) {
        showStatus(uploadStatus, validationError, 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('pdf_file', file);

    const isExcel = /\.(xlsx|xls)$/i.test(file.name);
    const submitBtn = uploadForm.querySelector('button[type="submit"]');
    
    showStatus(uploadStatus, `⏳ Parsing ${isExcel ? 'Excel Spreadsheet' : 'PDF Document'} & verifying student database...`, 'info');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>Processing...</span>';
    }
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            matchedStudents = result.matched_students || [];
            notFoundStudentsList = result.not_found_students || [];
            currentUploadToken = result.upload_token;
            
            // Save state in session storage so it persists across page views
            saveSessionData(result);

            displayResults(result);
            showStatus(uploadStatus, `✅ Processed successfully! ${result.total_matched} student(s) matched in database. (Status: Pending Allocation)`, 'success');
            
            if (quickJumpBanner) {
                quickJumpTitle.textContent = `🎉 Ingestion Complete: ${result.total_extracted} Extracted Seats`;
                quickJumpDesc.textContent = `${result.total_matched} matched in DB • Status: Pending Allocation. Click "Allocate Seating Arrangement" below to make it visible to students.`;
                quickJumpBanner.classList.add('visible');

                const quickAllocateBtn = document.getElementById('quickAllocateBtn');
                if (quickAllocateBtn && result.arrangement_id) {
                    quickAllocateBtn.style.display = 'inline-flex';
                    quickAllocateBtn.disabled = false;
                    quickAllocateBtn.className = 'btn btn-crimson btn-sm';
                    quickAllocateBtn.innerHTML = `
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        <span>Allocate Seating Arrangement</span>
                    `;
                    quickAllocateBtn.onclick = async () => {
                        await allocateArrangement(result.arrangement_id, quickAllocateBtn);
                    };
                }
            }
            loadArrangements();
        } else {
            showStatus(uploadStatus, `❌ ${result.error || 'Error processing file'}`, 'error');
        }
    } catch (error) {
        showStatus(uploadStatus, '❌ Network error occurred while uploading.', 'error');
        console.error('Upload error:', error);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>Process Seating</span>';
        }
    }
}

// =========================================================
// DISPLAY RESULTS & UPDATE SIDEBAR BADGES
// =========================================================
function displayResults(data) {
    // Summary KPI counters
    document.getElementById('totalExtracted').textContent = data.total_extracted;
    document.getElementById('totalMatched').textContent = data.total_matched;
    document.getElementById('totalNotFound').textContent = data.total_not_found;
    
    // Sidebar badges
    if (rosterBadge) rosterBadge.textContent = data.total_matched;
    
    const totalIssues = (data.not_found_students ? data.not_found_students.length : 0) + (invalidStudentsList ? invalidStudentsList.length : 0);
    if (auditBadge) {
        auditBadge.textContent = totalIssues;
        auditBadge.style.display = totalIssues > 0 ? 'inline-block' : 'none';
    }

    // Toggle Empty state in Roster tab
    if (rosterEmptyState) rosterEmptyState.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'block';

    // Toggle Audit state
    if (auditEmptyPrompt) auditEmptyPrompt.style.display = 'none';
    if (data.total_not_found === 0 && (!invalidStudentsList || invalidStudentsList.length === 0)) {
        if (auditCleanState) auditCleanState.style.display = 'flex';
    } else {
        if (auditCleanState) auditCleanState.style.display = 'none';
    }
    
    // Display matched students
    displayMatchedStudents(data.matched_students || []);
    
    // Display not found students
    displayNotFoundStudents(data.not_found_students || []);

    // Hide invalid emails initially
    const invalidSec = document.getElementById('invalidEmailSection');
    if (invalidSec) invalidSec.style.display = 'none';
    
    // Enable send buttons
    sendEmailsBtn.disabled = (data.matched_students || []).length === 0;
}

function displayMatchedStudents(students) {
    currentFilteredStudents = [...students];
    renderRosterRows(currentFilteredStudents);
    updateRosterCount(currentFilteredStudents.length, students.length);
}

function renderRosterRows(students) {
    const tableBody = document.querySelector('#matchedStudentsTable tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    if (students.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `<td colspan="10" style="text-align: center; padding: 20px; color: var(--ink-secondary);">
            No students match the search or filter criteria.
        </td>`;
        tableBody.appendChild(emptyRow);
        return;
    }

    students.forEach(student => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight: 700;">${escapeHtml(student.name)}</td>
            <td><span class="student-code">${escapeHtml(student.enrollment_number)}</span></td>
            <td><span style="font-weight: 600; color: #2563EB; font-size: 15px;">${escapeHtml(student.email)}</span></td>
            <td><span style="font-family: var(--font-mono); font-size: 14px;">${escapeHtml(student.phone || 'N/A')}</span></td>
            <td><span class="badge-tag">SEM ${escapeHtml(String(student.semester))}</span></td>
            <td><strong>${escapeHtml(student.block)}</strong></td>
            <td><span class="badge-tag blue">${escapeHtml(student.room)}</span></td>
            <td><span class="student-code">${escapeHtml(student.subject)}</span></td>
            <td>${escapeHtml(student.date)}</td>
            <td style="white-space: nowrap; font-size: 11.5px;">${escapeHtml(student.time)}</td>
        `;
        tableBody.appendChild(row);
    });
}

function updateRosterCount(filteredCount, totalCount) {
    if (!rosterFilterCount) return;
    if (filteredCount === totalCount) {
        rosterFilterCount.textContent = `Showing all ${totalCount} students`;
    } else {
        rosterFilterCount.textContent = `Showing ${filteredCount} of ${totalCount} students`;
    }
}

function displayNotFoundStudents(notFoundList) {
    const notFoundSection = document.getElementById('notFoundSection');
    const notFoundListElement = document.getElementById('notFoundList');
    
    if (notFoundList && notFoundList.length > 0) {
        if (notFoundCountBadge) notFoundCountBadge.textContent = notFoundList.length;
        notFoundListElement.innerHTML = notFoundList.map(enrollment => 
            `<span class="not-found-item">${escapeHtml(enrollment)}</span>`
        ).join('');
        notFoundSection.style.display = 'block';
    } else {
        notFoundSection.style.display = 'none';
    }
}

function displayInvalidEmailStudents(invalidList) {
    const section = document.getElementById('invalidEmailSection');
    const listEl  = document.getElementById('invalidEmailList');
    invalidStudentsList = invalidList || [];

    if (!invalidList || invalidList.length === 0) {
        if (section) section.style.display = 'none';
        return;
    }

    if (invalidEmailCountBadge) invalidEmailCountBadge.textContent = invalidList.length;

    const totalIssues = notFoundStudentsList.length + invalidList.length;
    if (auditBadge) {
        auditBadge.textContent = totalIssues;
        auditBadge.style.display = 'inline-block';
    }

    if (auditCleanState) auditCleanState.style.display = 'none';
    if (auditEmptyPrompt) auditEmptyPrompt.style.display = 'none';

    listEl.innerHTML = invalidList.map(item => `
        <div class="invalid-email-card">
            <div class="invalid-email-icon">⚠️</div>
            <div class="invalid-email-details">
                <div class="student-name">${escapeHtml(item.name)}</div>
                <div class="student-enroll">Enrollment: ${escapeHtml(item.enrollment_number)}</div>
                <div class="student-email">
                    ${item.email ? `Email: <strong>${escapeHtml(item.email)}</strong>` : 'No email address on record'}
                </div>
                <div class="invalid-reason">${escapeHtml(item.reason)}</div>
            </div>
        </div>
    `).join('');

    section.style.display = 'block';
}

// =========================================================
// SEND EMAILS HANDLER
// =========================================================
async function handleSendEmails() {
    if (matchedStudents.length === 0) {
        showStatus(messageStatus, '⚠️ No matched students to send emails to. Please upload a seating file first.', 'error');
        return;
    }
    
    currentMessageType = 'email';
    progressTitle.innerHTML = '<span>Sending Emails...</span>';
    const progressModeBadge = document.getElementById('progressModeBadge');
    if (progressModeBadge) progressModeBadge.textContent = 'Email';
    
    // Automatically switch to Dispatch Center view
    switchView('view-dispatch');
    
    progressSection.style.display = 'block';
    messageStatus.style.display = 'none';
    resetProgressDisplay();
    
    sendEmailsBtn.disabled = true;
    cancelBtn.style.display = 'inline-block';
    
    try {
        const response = await fetch('/send_emails', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ upload_token: currentUploadToken })
        });
        
        const result = await response.json();

        if (result.invalid_students && result.invalid_students.length > 0) {
            displayInvalidEmailStudents(result.invalid_students);
        }
        
        if (result.success) {
            const validCount   = result.total_students;
            const invalidCount = result.invalid_students ? result.invalid_students.length : 0;
            if (invalidCount > 0) {
                showStatus(
                    messageStatus,
                    `⚠️ ${invalidCount} student(s) skipped (invalid/missing email). Broadcasting to ${validCount} verified email address(es)...`,
                    'info'
                );
            }
            currentMessageSession = result.session_id;
            startProgressTracking(result.session_id, 'email');
        } else {
            showStatus(messageStatus, result.error || 'Could not start sending emails. Please try again.', 'error');
            resetMessageControls();
        }
    } catch (error) {
        showStatus(messageStatus, 'Network error. Please check your connection and try again.', 'error');
        console.error('Email sending start error:', error);
        resetMessageControls();
    }
}

// =========================================================
// CANCEL BROADCAST
// =========================================================
async function handleCancel() {
    if (!currentMessageSession || !currentMessageType) return;
    
    try {
        await fetch(`/cancel_emails/${currentMessageSession}`, { method: 'POST' });
        
        if (window.progressInterval) clearInterval(window.progressInterval);
        
        document.getElementById('currentStatus').innerHTML = '<span class="status-prompt-symbol">&gt;</span> 🚫 Broadcast was cancelled by user.';
        resetMessageControls();
        showStatus(messageStatus, 'Broadcast cancelled by user.', 'info');
    } catch (error) {
        console.error('Cancel error:', error);
    }
}

// =========================================================
// PROGRESS TRACKING & REAL-TIME POLLING
// =========================================================
function startProgressTracking(sessionId, messageType) {
    if (window.progressInterval) clearInterval(window.progressInterval);
    
    const endpoint = 'email_progress';
    
    window.progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/${endpoint}/${sessionId}`);
            
            if (response.ok) {
                const progress = await response.json();
                updateProgressDisplay(progress, messageType);
                
                if (progress.completed) {
                    clearInterval(window.progressInterval);
                    resetMessageControls();
                }
            } else {
                clearInterval(window.progressInterval);
                resetMessageControls();
            }
        } catch (error) {
            console.error(`${messageType} progress tracking error:`, error);
            clearInterval(window.progressInterval);
            resetMessageControls();
        }
    }, 500);
}

function updateProgressDisplay(progress, messageType) {
    const percentage = progress.total > 0 ? (progress.current / progress.total) * 100 : 0;
    document.getElementById('progressBarFill').style.width = `${percentage}%`;
    document.getElementById('progressText').textContent = `${progress.current} / ${progress.total} (${Math.round(percentage)}%)`;
    
    document.getElementById('totalCount').textContent = progress.total;
    document.getElementById('currentCount').textContent = progress.current;
    document.getElementById('sentCount').textContent = progress.sent;
    document.getElementById('failedCount').textContent = progress.failed;
    
    document.getElementById('currentStatus').innerHTML = `<span class="status-prompt-symbol">&gt;</span> <span>${escapeHtml(progress.status)}</span>`;
    
    const failedKey = messageType === 'email' ? 'failed_emails' : 'failed_messages';
    if (progress.failed > 0 && progress[failedKey] && progress[failedKey].length > 0) {
        displayFailedMessages(progress[failedKey], messageType);
    }
}

function displayFailedMessages(failedMessages, messageType) {
    const failedSection = document.getElementById('failedMessagesList');
    const failedContent = document.getElementById('failedMessagesContent');
    
    failedContent.innerHTML = failedMessages.map(item => {
        if (messageType === 'email') {
            return `<div class="failed-email-item">
                <strong>${escapeHtml(item.name)}</strong> (${escapeHtml(item.enrollment)})<br>
                <small style="color: #991B1B;">Reason: ${escapeHtml(item.error)}</small>
            </div>`;
        } else {
            return `<div class="failed-email-item">
                <strong>${escapeHtml(item.phone)}</strong><br>
                <small style="color: #991B1B;">Reason: ${escapeHtml(item.error)}</small>
            </div>`;
        }
    }).join('');
    
    failedSection.style.display = 'block';
}

function resetProgressDisplay() {
    document.getElementById('progressBarFill').style.width = '0%';
    document.getElementById('progressText').textContent = '0 / 0';
    document.getElementById('totalCount').textContent = '0';
    document.getElementById('currentCount').textContent = '0';
    document.getElementById('sentCount').textContent = '0';
    document.getElementById('failedCount').textContent = '0';
    document.getElementById('currentStatus').innerHTML = '<span class="status-prompt-symbol">&gt;</span> <span>Ready to dispatch...</span>';
    document.getElementById('failedMessagesList').style.display = 'none';
}

function resetMessageControls() {
    sendEmailsBtn.disabled = false;
    cancelBtn.style.display = 'none';
    currentMessageSession = null;
    currentMessageType = null;
    
    if (window.progressInterval) clearInterval(window.progressInterval);
}

// =========================================================
// SEARCH & FILTER FOR ROSTER
// =========================================================
function setupRosterSearchFilter() {
    if (!rosterSearchInput || !rosterSemFilter) return;

    function applyFilter() {
        const query = rosterSearchInput.value.toLowerCase().trim();
        const sem = rosterSemFilter.value;

        currentFilteredStudents = matchedStudents.filter(student => {
            const matchesQuery = !query || 
                (student.name && student.name.toLowerCase().includes(query)) ||
                (student.enrollment_number && String(student.enrollment_number).includes(query)) ||
                (student.room && student.room.toLowerCase().includes(query)) ||
                (student.block && student.block.toLowerCase().includes(query)) ||
                (student.subject && student.subject.toLowerCase().includes(query)) ||
                (student.email && student.email.toLowerCase().includes(query));

            const matchesSem = (sem === 'all') || (String(student.semester) === String(sem));
            return matchesQuery && matchesSem;
        });

        renderRosterRows(currentFilteredStudents);
        updateRosterCount(currentFilteredStudents.length, matchedStudents.length);
    }

    rosterSearchInput.addEventListener('input', applyFilter);
    rosterSemFilter.addEventListener('change', applyFilter);
}

// =========================================================
// EXPORT UTILITIES
// =========================================================
function setupExportUtilities() {
    if (copyRosterBtn) {
        copyRosterBtn.addEventListener('click', () => {
            if (matchedStudents.length === 0) {
                alert('No student records loaded to copy.');
                return;
            }
            
            const rows = currentFilteredStudents.map(s => 
                `${s.name}\t${s.enrollment_number}\t${s.email}\tSEM ${s.semester}\tBlock ${s.block}\tRoom ${s.room}\t${s.subject}\t${s.date}\t${s.time}`
            );
            
            const textToCopy = "Name\tEnrollment\tEmail\tSemester\tBlock\tRoom\tSubject\tDate\tTime\n" + rows.join('\n');
            navigator.clipboard.writeText(textToCopy).then(() => {
                const originalText = copyRosterBtn.textContent;
                copyRosterBtn.textContent = '✅ Copied!';
                setTimeout(() => { copyRosterBtn.textContent = originalText; }, 2000);
            });
        });
    }

    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            if (matchedStudents.length === 0) {
                alert('No student records loaded to export.');
                return;
            }
            
            const headers = ["Name", "Enrollment", "Email", "Phone", "Semester", "Block", "Room", "Subject", "Date", "Time"];
            const rows = currentFilteredStudents.map(s => [
                `"${(s.name || '').replace(/"/g, '""')}"`,
                `"${s.enrollment_number || ''}"`,
                `"${s.email || ''}"`,
                `"${s.phone || ''}"`,
                `"${s.semester || ''}"`,
                `"${s.block || ''}"`,
                `"${s.room || ''}"`,
                `"${s.subject || ''}"`,
                `"${s.date || ''}"`,
                `"${s.time || ''}"`
            ]);
            
            const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
            const link = document.createElement("a");
            link.setAttribute("href", encodeURI(csvContent));
            link.setAttribute("download", `exam_seating_roster_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    if (copyNotFoundBtn) {
        copyNotFoundBtn.addEventListener('click', () => {
            if (!notFoundStudentsList || notFoundStudentsList.length === 0) return;
            const text = notFoundStudentsList.join(', ');
            navigator.clipboard.writeText(text).then(() => {
                const originalText = copyNotFoundBtn.textContent;
                copyNotFoundBtn.textContent = '✅ Copied Numbers!';
                setTimeout(() => { copyNotFoundBtn.textContent = originalText; }, 2000);
            });
        });
    }
}

// =========================================================
// DATA PERSISTENCE
// =========================================================
function saveSessionData(data) {
    try {
        sessionStorage.setItem('examdesk_state', JSON.stringify({
            data: data,
            token: currentUploadToken
        }));
    } catch (e) {
        console.warn('SessionStorage quota exceeded or unavailable', e);
    }
}

function restoreSessionData() {
    try {
        const saved = sessionStorage.getItem('examdesk_state');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed && parsed.data) {
                matchedStudents = parsed.data.matched_students || [];
                notFoundStudentsList = parsed.data.not_found_students || [];
                currentUploadToken = parsed.token;
                displayResults(parsed.data);
            }
        }
    } catch (e) {
        console.warn('Could not restore session state', e);
    }
}

// =========================================================
// HELPERS
// =========================================================
function showStatus(element, message, type) {
    if (!element) return;
    element.className = `status ${type}`;
    element.innerHTML = message;
    element.style.display = 'block';
    
    if (type === 'info') {
        setTimeout(() => { element.style.display = 'none'; }, 6000);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function validateFile(file) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedExtensions = ['.pdf', '.xlsx', '.xls'];
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));

    if (!allowedExtensions.includes(ext)) {
        return '⚠️ Please select a PDF or Excel (.xlsx / .xls) file only.';
    }

    if (file.size > maxSize) {
        return '⚠️ File size must be less than 16MB.';
    }

    return null;
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// =========================================================
// SEATING ARRANGEMENTS MANAGEMENT
// =========================================================
let uploadedArrangements = [];

async function loadArrangements() {
    const tableBody = document.getElementById('arrangementsTableBody');
    const emptyState = document.getElementById('arrangementsEmptyState');
    const badge = document.getElementById('arrangementsBadge');

    try {
        const response = await fetch('/api/arrangements');
        const data = await response.json();

        if (data.success) {
            uploadedArrangements = data.arrangements || [];
            if (badge) badge.textContent = uploadedArrangements.length;

            if (tableBody) {
                renderArrangementsTable(uploadedArrangements);
            }
        }
    } catch (err) {
        console.error('Error fetching arrangements:', err);
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 30px; color: var(--color-danger);">
                        ⚠️ Failed to load seating arrangements. Please check your connection.
                    </td>
                </tr>
            `;
        }
    }
}

function renderArrangementsTable(arrangements) {
    const tableBody = document.getElementById('arrangementsTableBody');
    const emptyState = document.getElementById('arrangementsEmptyState');
    const table = document.getElementById('arrangementsTable');

    if (!tableBody) return;

    if (!arrangements || arrangements.length === 0) {
        tableBody.innerHTML = '';
        if (table) table.style.display = 'none';
        if (emptyState) emptyState.style.display = 'flex';
        return;
    }

    if (table) table.style.display = 'table';
    if (emptyState) emptyState.style.display = 'none';

    tableBody.innerHTML = arrangements.map((arr, idx) => {
        const isAllocated = arr.is_allocated;
        const statusHtml = isAllocated
            ? `<span class="badge-status-pill badge-allocated"><span class="status-dot green"></span> Allocated to Students</span>`
            : `<span class="badge-status-pill badge-pending"><span class="status-dot amber"></span> Pending (Not Allocated)</span>`;

        const allocateBtnHtml = isAllocated
            ? `<button class="btn btn-secondary btn-sm" disabled style="opacity: 0.7; cursor: default;">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span>Allocated</span>
               </button>`
            : `<button class="btn btn-crimson btn-sm btn-allocate-arr" data-id="${arr.id}" onclick="allocateArrangement(${arr.id}, this)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span>Allocate Seating</span>
               </button>`;

        const deleteBtnHtml = `
            <button class="btn btn-secondary btn-sm btn-delete-arr" data-id="${arr.id}" data-filename="${escapeHtml(arr.filename)}" onclick="deleteArrangement(${arr.id}, '${escapeHtml(arr.filename).replace(/'/g, "\\'")}', this)">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                <span>Delete</span>
            </button>
        `;

        return `
            <tr class="arrangement-row ${isAllocated ? 'row-allocated' : 'row-pending'}">
                <td style="font-weight: 600; color: var(--text-secondary);">${idx + 1}</td>
                <td>
                    <div style="font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                        <a href="#" title="Click to preview file"
                           onclick="event.preventDefault(); openExcelPreview(${arr.id}, '${escapeHtml(arr.filename).replace(/'/g, "\\'")}');"
                           style="color: #2563EB; text-decoration: none; font-weight: 700; transition: all 0.2s ease; cursor: pointer;"
                           onmouseover="this.style.textDecoration='underline'; this.style.color='#1D4ED8';"
                           onmouseout="this.style.textDecoration='none'; this.style.color='#2563EB';">
                            ${escapeHtml(arr.filename)}
                        </a>
                    </div>
                    ${arr.allocated_at ? `<div style="font-size: 11.5px; color: var(--text-secondary); margin-top: 2px;">Allocated: ${escapeHtml(arr.allocated_at)}</div>` : ''}
                </td>
                <td style="color: var(--text-secondary); font-size: 13px;">${escapeHtml(arr.uploaded_at) || '—'}</td>
                <td>
                    <span class="badge-count-pill">${arr.total_students} Students</span>
                </td>
                <td>${statusHtml}</td>
                <td style="text-align: right;">
                    <div style="display: inline-flex; gap: 8px; justify-content: flex-end; align-items: center;">
                        ${allocateBtnHtml}
                        ${deleteBtnHtml}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function allocateArrangement(id, btnElement) {
    const statusContainer = document.getElementById('arrangementsActionStatus');
    if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `<span>Allocating...</span>`;
    }

    try {
        const response = await fetch(`/api/arrangements/${id}/allocate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();

        if (result.success) {
            showStatus(statusContainer, `✅ ${result.message}`, 'success');
            if (btnElement) {
                btnElement.className = 'btn btn-secondary btn-sm';
                btnElement.disabled = true;
                btnElement.style.opacity = '0.7';
                btnElement.innerHTML = `
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>Allocated</span>
                `;
            }

            const quickAllocateBtn = document.getElementById('quickAllocateBtn');
            if (quickAllocateBtn) {
                quickAllocateBtn.disabled = true;
                quickAllocateBtn.className = 'btn btn-secondary btn-sm';
                quickAllocateBtn.innerHTML = `<span>✓ Allocated to Students</span>`;
            }
            if (quickJumpDesc) {
                quickJumpDesc.textContent = '✅ Seating arrangement successfully allocated to students!';
            }

            await loadArrangements();
        } else {
            showStatus(statusContainer, `❌ ${result.error || 'Failed to allocate arrangement.'}`, 'error');
            if (btnElement) {
                btnElement.disabled = false;
                btnElement.innerHTML = `<span>Allocate Seating</span>`;
            }
        }
    } catch (err) {
        console.error('Error allocating arrangement:', err);
        showStatus(statusContainer, '❌ Network error allocating arrangement.', 'error');
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `<span>Allocate Seating</span>`;
        }
    }
}

async function deleteArrangement(id, filename, btnElement) {
    const statusContainer = document.getElementById('arrangementsActionStatus');
    const confirmed = confirm(`Are you sure you want to delete the seating arrangement "${filename}"?\n\nThis will remove all associated student seat allocations.`);
    if (!confirmed) return;

    if (btnElement) {
        btnElement.disabled = true;
        btnElement.innerHTML = `<span>Deleting...</span>`;
    }

    try {
        const response = await fetch(`/api/arrangements/${id}/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();

        if (result.success) {
            showStatus(statusContainer, `🗑️ ${result.message}`, 'success');
            await loadArrangements();
        } else {
            showStatus(statusContainer, `❌ ${result.error || 'Failed to delete arrangement.'}`, 'error');
            if (btnElement) {
                btnElement.disabled = false;
                btnElement.innerHTML = `<span>Delete</span>`;
            }
        }
    } catch (err) {
        console.error('Error deleting arrangement:', err);
        showStatus(statusContainer, '❌ Network error deleting arrangement.', 'error');
        if (btnElement) {
            btnElement.disabled = false;
            btnElement.innerHTML = `<span>Delete</span>`;
        }
    }
}

// =========================================================
// CUSTOM CURSOR EFFECT (Curzr - Arrow Pointer)
// Initializes after DOM is ready and follows the mouse.
// =========================================================

class ArrowPointer {
  constructor() {
    this.root = document.body
    this.cursor = document.querySelector(".curzr-arrow-pointer")

    this.position = {
      distanceX: 0,
      distanceY: 0,
      distance: 0,
      pointerX: 0,
      pointerY: 0,
    }
    this.previousPointerX = 0
    this.previousPointerY = 0
    this.angle = 0
    this.previousAngle = 0
    this.angleDisplace = 0
    this.degrees = 57.296
    this.cursorSize = 20

    this.cursorStyle = {
      boxSizing: 'border-box',
      position: 'fixed',
      top: '0px',
      left: '0px',
      transform: 'translate(0, 0)',
      zIndex: '2147483647',
      width: `${this.cursorSize}px`,
      height: `${this.cursorSize}px`,
      transition: '250ms, transform 100ms',
      userSelect: 'none',
      pointerEvents: 'none',
    }

    this.init(this.cursor, this.cursorStyle)
  }

  init(el, style) {
    if (!el) return
    Object.assign(el.style, style)
    setTimeout(() => {
      el.removeAttribute("hidden")
    }, 300)
    el.style.opacity = 1
  }

  move(event) {
    if (!this.cursor) return
    this.previousPointerX = this.position.pointerX
    this.previousPointerY = this.position.pointerY
    this.position.pointerX = event.clientX
    this.position.pointerY = event.clientY
    this.position.distanceX = this.previousPointerX - this.position.pointerX
    this.position.distanceY = this.previousPointerY - this.position.pointerY
    this.distance = Math.sqrt(
      this.position.distanceY ** 2 + this.position.distanceX ** 2
    )

    this.cursor.style.transform = `translate3d(${this.position.pointerX}px, ${this.position.pointerY}px, 0)`

    if (this.distance > 1) {
      this.rotate(this.position)
    } else {
      this.cursor.style.transform += ` rotate(${this.angleDisplace}deg)`
    }
  }

  rotate(position) {
    let unsortedAngle =
      Math.atan(Math.abs(position.distanceY) / Math.abs(position.distanceX)) *
      this.degrees
    this.previousAngle = this.angle

    if (position.distanceX <= 0 && position.distanceY >= 0) {
      this.angle = 90 - unsortedAngle + 0
    } else if (position.distanceX < 0 && position.distanceY < 0) {
      this.angle = unsortedAngle + 90
    } else if (position.distanceX >= 0 && position.distanceY <= 0) {
      this.angle = 90 - unsortedAngle + 180
    } else if (position.distanceX > 0 && position.distanceY > 0) {
      this.angle = unsortedAngle + 270
    }

    if (isNaN(this.angle)) {
      this.angle = this.previousAngle
    } else {
      if (this.angle - this.previousAngle <= -270) {
        this.angleDisplace += 360 + this.angle - this.previousAngle
      } else if (this.angle - this.previousAngle >= 270) {
        this.angleDisplace += this.angle - this.previousAngle - 360
      } else {
        this.angleDisplace += this.angle - this.previousAngle
      }
    }
    this.cursor.style.left = `${-this.cursorSize / 2}px`
    this.cursor.style.top = `0px`
    this.cursor.style.transform += ` rotate(${this.angleDisplace}deg)`
  }

  click() {
    if (!this.cursor) return
    this.cursor.style.transform += ` scale(0.75)`
    setTimeout(() => {
      this.cursor.style.transform = this.cursor.style.transform.replace(
        ` scale(0.75)`,
        ''
      )
    }, 35)
  }

  hidden() {
    if (!this.cursor) return
    this.cursor.style.opacity = 0
    setTimeout(() => {
      this.cursor.setAttribute("hidden", "hidden")
    }, 500)
  }
}

// Boot cursor after DOM is ready (only on devices with fine pointer / mouse)
;(function initCursor() {
  // If device is touch-primary without fine pointer, keep native interaction
  if (window.matchMedia && window.matchMedia('(pointer: coarse)').matches && !window.matchMedia('(pointer: fine)').matches) {
    return
  }

  const el = document.querySelector('.curzr-arrow-pointer')
  if (!el) return

  const cursor = new ArrowPointer()

  document.addEventListener('mousemove', function (event) {
    cursor.move(event)
  })

  document.addEventListener('click', function () {
    cursor.click()
  })

  // Disable if user touches screen
  document.addEventListener('touchstart', function () {
    el.style.display = 'none'
  }, { once: true })
})()


// =========================================================
// EXCEL LIVE PREVIEW MODAL
// =========================================================

let _previewSheets = [];   // cache all sheets from last fetch
let _activeSheetIdx = 0;   // currently displayed sheet index

function openExcelPreview(arrangementId, filename) {
    const overlay   = document.getElementById('excelPreviewOverlay');
    const loading   = document.getElementById('excelModalLoading');
    const errorBox  = document.getElementById('excelModalError');
    const errorMsg  = document.getElementById('excelModalErrorMsg');
    const body      = document.getElementById('excelModalBody');
    const tabsBar   = document.getElementById('excelSheetTabs');
    const fileLabel = document.getElementById('excelModalFilename');
    const metaLabel = document.getElementById('excelModalMeta');
    const rowCount  = document.getElementById('excelModalRowCount');
    const dlBtn     = document.getElementById('excelModalDownloadBtn');

    // Reset UI
    fileLabel.textContent = filename;
    metaLabel.textContent = 'Excel Spreadsheet • Loading…';
    loading.style.display  = 'flex';
    errorBox.style.display = 'none';
    body.style.display     = 'none';
    tabsBar.innerHTML      = '';
    rowCount.textContent   = '';
    dlBtn.href = `/api/arrangements/${arrangementId}/download`;
    dlBtn.setAttribute('download', filename);

    // Open overlay
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';

    // Fetch preview data
    fetch(`/api/arrangements/${arrangementId}/preview`)
        .then(r => r.json())
        .then(data => {
            loading.style.display = 'none';

            if (!data.success || !data.sheets || data.sheets.length === 0) {
                errorMsg.textContent = data.error || 'No data found in file.';
                errorBox.style.display = 'flex';
                return;
            }

            _previewSheets  = data.sheets;
            _activeSheetIdx = 0;
            metaLabel.textContent = `Excel Spreadsheet • ${data.sheets.length} sheet${data.sheets.length > 1 ? 's' : ''}`;

            // Build sheet tabs
            data.sheets.forEach((sheet, idx) => {
                const tab = document.createElement('button');
                tab.className = 'excel-sheet-tab' + (idx === 0 ? ' active' : '');
                tab.textContent = sheet.name;
                tab.onclick = () => switchSheet(idx);
                tabsBar.appendChild(tab);
            });

            body.style.display = 'block';
            renderSheet(0);
        })
        .catch(err => {
            loading.style.display  = 'none';
            errorMsg.textContent   = 'Network error: ' + err.message;
            errorBox.style.display = 'flex';
        });
}

function switchSheet(idx) {
    _activeSheetIdx = idx;

    // Update tab active state
    document.querySelectorAll('.excel-sheet-tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === idx);
    });

    renderSheet(idx);
}

function renderSheet(idx) {
    const wrap     = document.getElementById('excelTableWrap');
    const rowCount = document.getElementById('excelModalRowCount');
    const sheet    = _previewSheets[idx];

    if (!sheet || !sheet.rows || sheet.rows.length === 0) {
        wrap.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-muted);font-weight:600;">Sheet is empty</div>';
        rowCount.textContent = '0 rows';
        return;
    }

    const allRows  = sheet.rows;

    // Build table HTML — use ALL rows including first as header
    // Find first non-empty row as actual header
    let headerIdx = 0;
    for (let i = 0; i < allRows.length; i++) {
        if (allRows[i].some(c => c !== '')) { headerIdx = i; break; }
    }
    const header   = allRows[headerIdx];
    const dataRows = allRows.slice(headerIdx + 1);

    // Count non-empty data rows
    const nonEmpty = dataRows.filter(r => r.some(c => c !== ''));
    rowCount.textContent = `${nonEmpty.length} rows × ${header.length} columns`;

    let html = '<table class="excel-preview-table"><thead><tr>';
    html += '<th class="row-num">#</th>';
    header.forEach(cell => {
        html += `<th>${escapeHtml(cell)}</th>`;
    });
    html += '</tr></thead><tbody>';

    let visibleRow = 0;
    let prevWasEmpty = false;

    dataRows.forEach((row) => {
        const isEmpty = !row.some(c => c !== '');

        if (isEmpty) {
            // Only insert ONE separator row between groups, skip consecutive empties
            if (!prevWasEmpty) {
                html += `<tr class="excel-separator-row"><td class="row-num"></td>${header.map(() => '<td></td>').join('')}</tr>`;
            }
            prevWasEmpty = true;
            return;
        }

        prevWasEmpty = false;
        visibleRow++;
        html += `<tr><td class="row-num">${visibleRow}</td>`;
        row.forEach(cell => {
            html += `<td>${escapeHtml(cell)}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    wrap.innerHTML = html;
}

function closeExcelPreview(event) {
    // Close only if clicking backdrop or close button (not inside modal)
    if (event && event.target !== document.getElementById('excelPreviewOverlay')) return;
    _forceCloseExcelPreview();
}

function _forceCloseExcelPreview() {
    const overlay = document.getElementById('excelPreviewOverlay');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
    _previewSheets  = [];
    _activeSheetIdx = 0;
}

// Close on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') _forceCloseExcelPreview();
});
