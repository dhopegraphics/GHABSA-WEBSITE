/* =====================================================
   EXPENSE MANAGEMENT ADMIN - INTERACTIVE FEATURES
   ===================================================== */

(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initExpenseDashboard();
        initChartAnimations();
        initFormEnhancements();
        initQuickActions();
    });

    /**
     * Initialize the expense dashboard
     */
    function initExpenseDashboard() {
        const dashboard = document.querySelector('.expense-dashboard');
        if (!dashboard) return;

        // Animate counter numbers
        animateCounters();

        // Initialize tooltips
        initTooltips();
    }

    /**
     * Animate number counters
     */
    function animateCounters() {
        const counters = document.querySelectorAll('.card-value, .amount-display');
        
        counters.forEach(counter => {
            const text = counter.textContent;
            const matches = text.match(/[\d,]+\.?\d*/);
            
            if (matches) {
                const targetValue = parseFloat(matches[0].replace(/,/g, ''));
                const prefix = text.substring(0, text.indexOf(matches[0]));
                const suffix = text.substring(text.indexOf(matches[0]) + matches[0].length);
                
                animateValue(counter, 0, targetValue, 1000, prefix, suffix);
            }
        });
    }

    /**
     * Animate a numeric value
     */
    function animateValue(element, start, end, duration, prefix = '', suffix = '') {
        const startTimestamp = performance.now();
        
        const step = (timestamp) => {
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const easeProgress = easeOutExpo(progress);
            const current = start + (end - start) * easeProgress;
            
            element.textContent = prefix + formatNumber(current) + suffix;
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        
        window.requestAnimationFrame(step);
    }

    /**
     * Easing function
     */
    function easeOutExpo(x) {
        return x === 1 ? 1 : 1 - Math.pow(2, -10 * x);
    }

    /**
     * Format number with commas and decimals
     */
    function formatNumber(num) {
        return num.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Initialize chart animations
     */
    function initChartAnimations() {
        // Animate progress bars
        const progressBars = document.querySelectorAll('.progress-bar-fill');
        
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = width;
            }, 300);
        });

        // Animate category pills on hover
        const categoryPills = document.querySelectorAll('.category-pill');
        categoryPills.forEach(pill => {
            pill.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.05) translateY(-2px)';
            });
            pill.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1) translateY(0)';
            });
        });
    }

    /**
     * Initialize tooltips
     */
    function initTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        
        tooltipElements.forEach(element => {
            const titleText = element.getAttribute('title');
            if (!titleText) return;
            
            element.removeAttribute('title');
            element.setAttribute('data-tooltip', titleText);
            
            element.addEventListener('mouseenter', showTooltip);
            element.addEventListener('mouseleave', hideTooltip);
        });
    }

    function showTooltip(e) {
        const text = e.target.getAttribute('data-tooltip');
        if (!text) return;
        
        const tooltip = document.createElement('div');
        tooltip.className = 'expense-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: fixed;
            background: #1f2937;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            max-width: 200px;
            z-index: 10000;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = e.target.getBoundingClientRect();
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
        tooltip.style.left = (rect.left + (rect.width - tooltip.offsetWidth) / 2) + 'px';
        
        e.target._tooltip = tooltip;
    }

    function hideTooltip(e) {
        if (e.target._tooltip) {
            e.target._tooltip.remove();
            delete e.target._tooltip;
        }
    }

    /**
     * Initialize form enhancements
     */
    function initFormEnhancements() {
        // Auto-format currency inputs
        const currencyInputs = document.querySelectorAll('input[name="amount"], input[name="allocated_amount"]');
        
        currencyInputs.forEach(input => {
            input.addEventListener('blur', function() {
                const value = parseFloat(this.value.replace(/,/g, ''));
                if (!isNaN(value)) {
                    this.value = value.toFixed(2);
                }
            });
        });

        // Category color preview
        const colorInput = document.querySelector('input[name="color"]');
        const iconInput = document.querySelector('input[name="icon"]');
        const nameInput = document.querySelector('input[name="name"]');
        
        if (colorInput && iconInput && nameInput) {
            const preview = document.createElement('div');
            preview.style.cssText = `
                margin-top: 10px;
                padding: 8px 16px;
                border-radius: 20px;
                display: inline-block;
                font-weight: 500;
                color: white;
            `;
            
            const updatePreview = () => {
                preview.style.backgroundColor = colorInput.value || '#6366f1';
                preview.textContent = `${iconInput.value || '💰'} ${nameInput.value || 'Category Name'}`;
            };
            
            colorInput.parentNode.appendChild(preview);
            
            [colorInput, iconInput, nameInput].forEach(input => {
                input.addEventListener('input', updatePreview);
            });
            
            updatePreview();
        }

        // Date range validation for budgets
        const startDateInput = document.querySelector('input[name="start_date"]');
        const endDateInput = document.querySelector('input[name="end_date"]');
        
        if (startDateInput && endDateInput) {
            endDateInput.addEventListener('change', function() {
                if (startDateInput.value && this.value) {
                    if (new Date(this.value) <= new Date(startDateInput.value)) {
                        alert('End date must be after start date');
                        this.value = '';
                    }
                }
            });
        }
    }

    /**
     * Initialize quick action buttons
     */
    function initQuickActions() {
        // Add quick filter buttons to expense list
        const resultList = document.querySelector('#result_list');
        if (!resultList) return;

        const filterContainer = document.createElement('div');
        filterContainer.className = 'quick-filters';
        filterContainer.style.cssText = `
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        `;

        const filters = [
            { label: '📋 All', status: '' },
            { label: '⏳ Pending', status: 'pending' },
            { label: '✅ Approved', status: 'approved' },
            { label: '💵 Paid', status: 'paid' },
            { label: '❌ Rejected', status: 'rejected' }
        ];

        filters.forEach(filter => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = filter.label;
            button.style.cssText = `
                padding: 6px 14px;
                border: none;
                border-radius: 20px;
                background: ${filter.status === '' ? '#667eea' : '#e5e7eb'};
                color: ${filter.status === '' ? 'white' : '#4b5563'};
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s ease;
            `;
            
            button.addEventListener('click', () => {
                const currentUrl = new URL(window.location.href);
                if (filter.status) {
                    currentUrl.searchParams.set('status__exact', filter.status);
                } else {
                    currentUrl.searchParams.delete('status__exact');
                }
                window.location.href = currentUrl.toString();
            });
            
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            });
            
            filterContainer.appendChild(button);
        });

        resultList.parentNode.insertBefore(filterContainer, resultList);
    }

    /**
     * Resend SMS notification via AJAX
     */
    window.resendExpenseSMS = function(expenseId) {
        if (!confirm('Are you sure you want to resend SMS notification to executives?')) {
            return;
        }
        
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = 'Sending...';
        button.disabled = true;
        
        fetch(`/api/expenses/${expenseId}/resend-sms/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.textContent = '✅ Sent!';
                button.style.background = '#10b981';
            } else {
                button.textContent = '❌ Failed';
                button.style.background = '#ef4444';
                alert('Failed to send SMS: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            button.textContent = '❌ Error';
            button.style.background = '#ef4444';
            console.error('SMS resend error:', error);
        })
        .finally(() => {
            setTimeout(() => {
                button.textContent = originalText;
                button.style.background = '';
                button.disabled = false;
            }, 3000);
        });
    };

    /**
     * Get CSRF cookie
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

})();
