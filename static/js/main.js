// Main JavaScript file for Face Recognition System

// Global variables
let currentPage = 1;
let itemsPerPage = 10;

// Utility functions
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

function showLoading(element) {
    if (element) {
        element.innerHTML = '<div class="spinner-border spinner-border-sm me-2" role="status"></div>Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPhoneNumber(phone) {
    if (!phone) return '';
    const cleaned = phone.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    return phone;
}

// Search and filter functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableId = this.dataset.table;
            const table = document.getElementById(tableId);
            
            if (table) {
                filterTable(table, searchTerm);
            }
        });
    });
}

function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Pagination functionality
function initializePagination() {
    const paginationContainers = document.querySelectorAll('.pagination-container');
    
    paginationContainers.forEach(container => {
        const tableId = container.dataset.table;
        const table = document.getElementById(tableId);
        
        if (table) {
            setupPagination(table, container);
        }
    });
}

function setupPagination(table, container) {
    const rows = table.querySelectorAll('tbody tr');
    const totalPages = Math.ceil(rows.length / itemsPerPage);
    
    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    renderPagination(container, totalPages, table);
}

function renderPagination(container, totalPages, table) {
    container.innerHTML = '';
    
    // Previous button
    const prevBtn = document.createElement('li');
    prevBtn.className = 'page-item';
    prevBtn.innerHTML = '<a class="page-link" href="#" data-page="prev">Previous</a>';
    container.appendChild(prevBtn);
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
        container.appendChild(pageItem);
    }
    
    // Next button
    const nextBtn = document.createElement('li');
    nextBtn.className = 'page-item';
    nextBtn.innerHTML = '<a class="page-link" href="#" data-page="next">Next</a>';
    container.appendChild(nextBtn);
    
    // Event listeners
    container.addEventListener('click', function(e) {
        e.preventDefault();
        if (e.target.classList.contains('page-link')) {
            const page = e.target.dataset.page;
            if (page === 'prev' && currentPage > 1) {
                currentPage--;
            } else if (page === 'next' && currentPage < totalPages) {
                currentPage++;
            } else if (page !== 'prev' && page !== 'next') {
                currentPage = parseInt(page);
            }
            
            showPage(table, currentPage);
            renderPagination(container, totalPages, table);
        }
    });
}

function showPage(table, page) {
    const rows = table.querySelectorAll('tbody tr');
    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    
    rows.forEach((row, index) => {
        if (index >= start && index < end) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Image preview functionality
function initializeImagePreview() {
    const imageInputs = document.querySelectorAll('.image-input');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            const preview = document.getElementById(this.dataset.preview);
            
            if (file && preview) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    });
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function showDeleteConfirmation(element, itemName) {
    const message = `Are you sure you want to delete ${itemName}? This action cannot be undone.`;
    confirmAction(message, () => {
        // Add loading state
        const originalText = element.innerHTML;
        showLoading(element);
        
        // Simulate delete action (replace with actual delete logic)
        setTimeout(() => {
            hideLoading(element, originalText);
            showNotification(`${itemName} deleted successfully`, 'success');
        }, 1000);
    });
}

// Data export functionality
function exportToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        
        cols.forEach(col => {
            rowData.push('"' + col.textContent.replace(/"/g, '""') + '"');
        });
        
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Auto-refresh functionality
function initializeAutoRefresh(interval = 30000) {
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    
    autoRefreshElements.forEach(element => {
        setInterval(() => {
            // Reload the page or specific content
            if (element.dataset.autoRefresh === 'page') {
                window.location.reload();
            } else if (element.dataset.autoRefresh === 'content') {
                // Reload specific content via AJAX
                loadContent(element);
            }
        }, interval);
    });
}

function loadContent(element) {
    const url = element.dataset.url;
    if (!url) return;
    
    fetch(url)
        .then(response => response.text())
        .then(html => {
            element.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading content:', error);
        });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveBtn = document.querySelector('.btn-save');
            if (saveBtn) saveBtn.click();
        }
        
        // Ctrl/Cmd + N to add new
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const addBtn = document.querySelector('.btn-add');
            if (addBtn) addBtn.click();
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
}

// Theme switching
function initializeThemeSwitcher() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (!themeToggle) return;
    
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', currentTheme);
    
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        showNotification(`Switched to ${newTheme} theme`, 'info');
    });
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializePagination();
    initializeFormValidation();
    initializeImagePreview();
    initializeAutoRefresh();
    initializeKeyboardShortcuts();
    initializeThemeSwitcher();
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card, .stats-card, .action-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Export functions for use in other scripts
window.FaceRecognitionUtils = {
    showNotification,
    showLoading,
    hideLoading,
    formatDate,
    formatPhoneNumber,
    confirmAction,
    exportToCSV,
    filterTable
};
