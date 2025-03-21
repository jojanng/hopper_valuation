// Features Menu Functionality
document.addEventListener('DOMContentLoaded', function() {
    const featuresMenu = document.querySelector('.features-menu');
    const featuresMenuBtn = document.querySelector('.features-menu-btn');
    const closeMenuBtn = document.querySelector('.close-menu-btn');

    function openFeaturesMenu() {
        featuresMenu.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeFeaturesMenu() {
        featuresMenu.classList.remove('active');
        document.body.style.overflow = '';
    }

    featuresMenuBtn.addEventListener('click', openFeaturesMenu);
    closeMenuBtn.addEventListener('click', closeFeaturesMenu);

    // Close menu when clicking outside
    featuresMenu.addEventListener('click', function(e) {
        if (e.target === featuresMenu) {
            closeFeaturesMenu();
        }
    });

    // Close menu on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && featuresMenu.classList.contains('active')) {
            closeFeaturesMenu();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Form submission
    const form = document.getElementById('valuation-form');
    const loadingIndicator = document.getElementById('loading');
    const resultsContainer = document.getElementById('results-container');
    const sensitivityCard = document.getElementById('sensitivity-card');
    const symbolInput = document.getElementById('symbol');
    const symbolSearchBtn = document.getElementById('symbol-search');
    
    // Update desired return display when the input changes
    const desiredReturnInput = document.getElementById('desired-return');
    if (desiredReturnInput) {
        desiredReturnInput.addEventListener('input', function() {
            updateDesiredReturnDisplay(this.value);
        });
        // Initialize with default value
        updateDesiredReturnDisplay(desiredReturnInput.value);
    }
    
    // Function to update the desired return display in multiple places
    function updateDesiredReturnDisplay(value) {
        const desiredReturnDisplay = document.getElementById('desired-return-display');
        const tableDesiredReturn = document.getElementById('table-desired-return');
        
        if (desiredReturnDisplay) {
            desiredReturnDisplay.textContent = value;
        }
        
        if (tableDesiredReturn) {
            tableDesiredReturn.textContent = value;
        }
    }
    
    // Custom entry price calculation
    const calculateEntryBtn = document.getElementById('calculate-entry');
    const customReturnInput = document.getElementById('custom-return');
    const entryPriceResult = document.getElementById('entry-price-result');
    
    // Add event listener for custom entry price calculation
    if (calculateEntryBtn) {
        calculateEntryBtn.addEventListener('click', calculateCustomEntryPrice);
    }
    
    // Function to calculate custom entry price
    function calculateCustomEntryPrice() {
        const customReturn = parseFloat(customReturnInput.value) / 100;
        const currentPrice = parseFloat(document.getElementById('current-price').textContent.replace(/[^0-9.-]+/g, ''));
        const years = parseInt(document.getElementById('years').value);
        
        // Get the weighted intrinsic value
        const weightedValueElement = document.querySelector('#valuation-summary tbody tr:last-child td:nth-child(2)');
        if (!weightedValueElement) {
            entryPriceResult.textContent = 'Please calculate valuation first';
            return;
        }
        
        const intrinsicValue = parseFloat(weightedValueElement.textContent.replace(/[^0-9.-]+/g, ''));
        
        // Calculate entry price for custom return
        const entryPrice = intrinsicValue / Math.pow(1 + customReturn, years);
        const discount = (currentPrice - entryPrice) / currentPrice * 100;
        
        // Update the result display
        entryPriceResult.innerHTML = `
            <strong>Entry Price for ${customReturn * 100}% Return:</strong> ${formatCurrency(entryPrice)}<br>
            <span class="${discount > 0 ? 'text-danger' : 'text-success'}">
                ${discount > 0 ? 'Discount needed: ' + discount.toFixed(2) + '%' : 'Current price is below entry price by ' + Math.abs(discount).toFixed(2) + '%'}
            </span>
        `;
    }
    
    // Initialize with default values
    updateWeightTotal();
    
    // Event listeners for weight inputs to ensure they sum to 100%
    document.getElementById('fcf-weight').addEventListener('input', updateWeightTotal);
    document.getElementById('eps-weight').addEventListener('input', updateWeightTotal);
    document.getElementById('ev-ebitda-weight').addEventListener('input', updateWeightTotal);
    
    // Toggle EV/EBITDA weight input based on checkbox
    document.getElementById('use-ev-ebitda').addEventListener('change', function() {
        const evEbitdaWeightInput = document.getElementById('ev-ebitda-weight');
        evEbitdaWeightInput.disabled = !this.checked;
        if (!this.checked) {
            evEbitdaWeightInput.value = 0;
        } else {
            evEbitdaWeightInput.value = 20;
        }
        updateWeightTotal();
    });
    
    // Symbol search button handler - now supports both showing the symbol list and direct search
    symbolSearchBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (symbolInput.value.trim() !== '') {
            // If there's text in the input, treat as direct search
            form.dispatchEvent(new Event('submit'));
        } else {
            // Otherwise show the symbol selector
            fetchSymbols();
        }
    });
    
    // Symbol input handler - trigger valuation on Enter key
    symbolInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            form.dispatchEvent(new Event('submit'));
        }
    });
    
    // Fetch available symbols
    function fetchSymbols() {
        fetch('/api/symbols')
            .then(response => response.json())
            .then(data => {
                if (data.symbols && data.symbols.length > 0) {
                    showSymbolSelector(data.symbols);
                }
            })
            .catch(error => {
                console.error('Error fetching symbols:', error);
                showErrorMessage('Error fetching symbols. Please try again later.');
            });
    }
    
    // Show symbol selector modal
    function showSymbolSelector(symbols) {
        // Remove existing modal if any
        const existingModal = document.getElementById('symbol-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal
        const modal = document.createElement('div');
        modal.id = 'symbol-modal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Select Stock Symbol</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <input type="text" class="form-control mb-3" id="symbol-search-input" placeholder="Filter symbols...">
                        <div class="list-group" id="symbol-list">
                            ${symbols.map(symbol => `<button type="button" class="list-group-item list-group-item-action symbol-item">${symbol}</button>`).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Initialize Bootstrap modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Symbol filter
        const symbolSearchInput = document.getElementById('symbol-search-input');
        symbolSearchInput.addEventListener('input', function() {
            const filter = this.value.toUpperCase();
            const items = document.getElementsByClassName('symbol-item');
            
            for (let i = 0; i < items.length; i++) {
                const symbol = items[i].textContent || items[i].innerText;
                if (symbol.toUpperCase().indexOf(filter) > -1) {
                    items[i].style.display = '';
                } else {
                    items[i].style.display = 'none';
                }
            }
        });
        
        // Symbol selection
        const symbolItems = document.getElementsByClassName('symbol-item');
        for (let i = 0; i < symbolItems.length; i++) {
            symbolItems[i].addEventListener('click', function() {
                const selectedSymbol = this.textContent || this.innerText;
                symbolInput.value = selectedSymbol;
                modalInstance.hide();
                
                // Trigger form submission to update valuation
                form.dispatchEvent(new Event('submit'));
            });
        }
    }
    
    // Function to show error message
    function showErrorMessage(message) {
        // Hide loading indicator
        loadingIndicator.classList.add('d-none');
        
        // Create error alert if it doesn't exist
        let errorAlert = document.getElementById('error-alert');
        if (!errorAlert) {
            errorAlert = document.createElement('div');
            errorAlert.id = 'error-alert';
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.setAttribute('role', 'alert');
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('data-bs-dismiss', 'alert');
            closeButton.setAttribute('aria-label', 'Close');
            
            errorAlert.appendChild(closeButton);
            
            // Insert before the form
            form.parentNode.insertBefore(errorAlert, form);
        }
        
        // Update error message
        errorAlert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Show the error alert
        errorAlert.classList.remove('d-none');
        
        // Scroll to error
        errorAlert.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Hide any existing error message
        const errorAlert = document.getElementById('error-alert');
        if (errorAlert) {
            errorAlert.classList.add('d-none');
        }
        
        // Show loading indicator
        loadingIndicator.classList.remove('d-none');
        resultsContainer.classList.add('d-none');
        
        // Get form data
        const formData = new FormData(form);
        const payload = {};
        
        // Convert form data to JSON payload
        for (const [key, value] of formData.entries()) {
            if (key === 'sensitivity' || key === 'use_ev_ebitda') {
                payload[key] = value === 'on';
            } else if (key !== 'symbol') {
                payload[key] = parseFloat(value);
            } else {
                payload[key] = value.toUpperCase();
            }
        }
        
        // Get projection years from select element
        const projectionYearsSelect = document.getElementById('projection-years');
        if (projectionYearsSelect) {
            payload.projection_years = parseInt(projectionYearsSelect.value);
        }
        
        // Ensure weights sum to 100%
        const totalWeight = payload.fcf_weight + payload.eps_weight + payload.ev_ebitda_weight;
        if (Math.abs(totalWeight - 100) > 0.01) {
            showErrorMessage('Valuation weights must sum to 100%. Please adjust your weights.');
            return;
        }
        
        // Make API call
        fetch('/api/valuation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Network response was not ok');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator and show results
            loadingIndicator.classList.add('d-none');
            resultsContainer.classList.remove('d-none');
            
            // Update UI with results
            updateMarketData(data.market_data, payload.symbol);
            updateValuationSummary(data.valuation_results, payload.desired_return);
            updateProjections(data.projections);
            createPriceProjectionChart(data.market_data.current_price, data.valuation_results.weighted_valuation.intrinsic_value, payload.years);
            
            // Handle sensitivity analysis if requested
            if (payload.sensitivity) {
                sensitivityCard.classList.remove('d-none');
                updateSensitivityAnalysis(data.sensitivity_analysis);
            } else {
                sensitivityCard.classList.add('d-none');
            }
            
            // Scroll to results
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.classList.add('d-none');
            
            // Show user-friendly error message
            if (error.message.includes("not found")) {
                showErrorMessage(`${error.message} Available symbols include: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, AMD, PLTR, ASML, JPM, V, JNJ, etc.`);
            } else {
                showErrorMessage('Error calculating valuation: ' + error.message);
            }
        });
    });
    
    // Function to update the weight total and validate
    function updateWeightTotal() {
        const fcfWeight = parseFloat(document.getElementById('fcf-weight').value) || 0;
        const epsWeight = parseFloat(document.getElementById('eps-weight').value) || 0;
        const evEbitdaWeight = parseFloat(document.getElementById('ev-ebitda-weight').value) || 0;
        
        const totalWeight = fcfWeight + epsWeight + evEbitdaWeight;
        
        // Update the weight total display
        const weightTotalElement = document.getElementById('weight-total');
        if (weightTotalElement) {
            weightTotalElement.textContent = totalWeight.toFixed(0) + '%';
            
            // Highlight if not 100%
            if (Math.abs(totalWeight - 100) > 0.01) {
                weightTotalElement.classList.add('text-danger');
                weightTotalElement.classList.remove('text-success');
            } else {
                weightTotalElement.classList.add('text-success');
                weightTotalElement.classList.remove('text-danger');
            }
        }
        
        // Visual feedback on weight total
        const submitButton = form.querySelector('button[type="submit"]');
        if (Math.abs(totalWeight - 100) > 0.01) {
            submitButton.classList.add('btn-danger');
            submitButton.classList.remove('btn-primary');
            submitButton.textContent = `Calculate Valuation (Weights: ${totalWeight.toFixed(0)}%)`;
        } else {
            submitButton.classList.remove('btn-danger');
            submitButton.classList.add('btn-primary');
            submitButton.textContent = 'Calculate Valuation';
        }
    }
    
    // Function to update market data display
    function updateMarketData(data, symbol) {
        // Update the title with the symbol
        const marketDataTitle = document.getElementById('market-data-title');
        if (marketDataTitle) {
            marketDataTitle.textContent = `${symbol} - Market Data`;
        }
        
        // Update market data values
        updateElementText('current-price', formatCurrency(data.current_price));
        updateElementText('shares-outstanding', formatNumber(data.shares_outstanding) + ' shares');
        updateElementText('fcf', formatCurrency(data.fcf, true));
        updateElementText('net-income', formatCurrency(data.net_income, true));
        updateElementText('ebitda', formatCurrency(data.ebitda, true));
        updateElementText('fcf-per-share', formatCurrency(data.fcf_per_share));
        updateElementText('eps', formatCurrency(data.eps));
        updateElementText('pe-ratio', data.pe_ratio.toFixed(2));
        updateElementText('net-debt', formatCurrency(data.net_debt, true));
    }
    
    // Helper function to safely update element text content
    function updateElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }
    
    // Function to update valuation summary
    function updateValuationSummary(results, desiredReturn) {
        const table = document.getElementById('valuation-summary');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        
        // Clear existing content
        tbody.innerHTML = '';
        
        // Update the calculation results section
        const returnFromToday = document.getElementById('return-from-today');
        const entryPriceDisplay = document.getElementById('entry-price-display');
        
        if (returnFromToday) {
            returnFromToday.textContent = formatPercentage(results.weighted_valuation.implied_return);
            returnFromToday.className = results.weighted_valuation.implied_return < 0 ? 'fw-bold text-danger' : 'fw-bold text-success';
        }
        
        if (entryPriceDisplay) {
            entryPriceDisplay.textContent = formatCurrency(results.weighted_valuation.entry_price);
        }
        
        // FCF-Based row
        const fcfRow = document.createElement('tr');
        fcfRow.innerHTML = `
            <td>FCF-Based</td>
            <td>${formatCurrency(results.fcf_valuation.intrinsic_value)}</td>
            <td>${formatCurrency(results.fcf_valuation.entry_price)}</td>
            <td class="${results.fcf_valuation.implied_return < 0 ? 'negative-value' : 'positive-value'}">${formatPercentage(results.fcf_valuation.implied_return)}</td>
        `;
        tbody.appendChild(fcfRow);
        
        // EPS-Based row
        const epsRow = document.createElement('tr');
        epsRow.innerHTML = `
            <td>EPS-Based</td>
            <td>${formatCurrency(results.eps_valuation.intrinsic_value)}</td>
            <td>${formatCurrency(results.eps_valuation.entry_price)}</td>
            <td class="${results.eps_valuation.implied_return < 0 ? 'negative-value' : 'positive-value'}">${formatPercentage(results.eps_valuation.implied_return)}</td>
        `;
        tbody.appendChild(epsRow);
        
        // EV/EBITDA-Based row (if available)
        if (results.ev_ebitda_valuation) {
            const evEbitdaRow = document.createElement('tr');
            evEbitdaRow.innerHTML = `
                <td>EV/EBITDA-Based</td>
                <td>${formatCurrency(results.ev_ebitda_valuation.intrinsic_value)}</td>
                <td>${formatCurrency(results.ev_ebitda_valuation.entry_price)}</td>
                <td class="${results.ev_ebitda_valuation.implied_return < 0 ? 'negative-value' : 'positive-value'}">${formatPercentage(results.ev_ebitda_valuation.implied_return)}</td>
            `;
            tbody.appendChild(evEbitdaRow);
        }
        
        // Weighted Average row
        const weightedRow = document.createElement('tr');
        weightedRow.className = 'table-primary';
        weightedRow.innerHTML = `
            <td><strong>Weighted Average</strong></td>
            <td><strong>${formatCurrency(results.weighted_valuation.intrinsic_value)}</strong></td>
            <td><strong>${formatCurrency(results.weighted_valuation.entry_price)}</strong></td>
            <td class="${results.weighted_valuation.implied_return < 0 ? 'negative-value' : 'positive-value'}"><strong>${formatPercentage(results.weighted_valuation.implied_return)}</strong></td>
        `;
        tbody.appendChild(weightedRow);
    }
    
    // Function to update projections
    function updateProjections(projections) {
        // 5-Year FCF Projections
        updateProjectionTable('fcf-projections', projections.fcf_projections);
        updateProjectionTable('eps-projections', projections.eps_projections);
        updateProjectionTable('ebitda-projections', projections.ebitda_projections);
        
        // Create projection charts
        createProjectionCharts(projections);
        
        // 2-Year Projections
        if (projections.two_year_targets) {
            updateElementText('fcf-2yr-value', formatCurrency(projections.two_year_targets.fcf.target_price));
            updateElementText('fcf-2yr-entry', formatCurrency(projections.two_year_targets.fcf.entry_price));
            updateElementText('fcf-2yr-implied', formatPercentage(projections.two_year_targets.fcf.implied_return));
            
            updateElementText('eps-2yr-value', formatCurrency(projections.two_year_targets.eps.target_price));
            updateElementText('eps-2yr-entry', formatCurrency(projections.two_year_targets.eps.entry_price));
            updateElementText('eps-2yr-implied', formatPercentage(projections.two_year_targets.eps.implied_return));
            
            updateElementText('weighted-2yr-value', formatCurrency(projections.two_year_targets.weighted.target_price));
            updateElementText('weighted-2yr-entry', formatCurrency(projections.two_year_targets.weighted.entry_price));
            updateElementText('weighted-2yr-implied', formatPercentage(projections.two_year_targets.weighted.implied_return));
        }
        
        // Quarterly projections
        if (projections.quarterly_projections) {
            const quarterlyTable = document.getElementById('quarterly-projections');
            if (quarterlyTable) {
                quarterlyTable.innerHTML = '';
                
                // Create header row
                const headerRow = document.createElement('tr');
                headerRow.classList.add('table-light');
                headerRow.innerHTML = '<th>Quarter</th><th>FCF/Share</th><th>EPS</th><th>EBITDA (B)</th>';
                quarterlyTable.appendChild(headerRow);
                
                // Add data rows
                projections.quarterly_projections.forEach(quarter => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${quarter.quarter}</td>
                        <td>${formatCurrency(quarter.fcf_per_share)}</td>
                        <td>${formatCurrency(quarter.eps)}</td>
                        <td>${formatCurrency(quarter.ebitda / 1e9, false, 2)}</td>
                    `;
                    quarterlyTable.appendChild(row);
                });
            }
        }
    }
    
    // Function to create projection charts
    function createProjectionCharts(projections) {
        // Destroy existing charts if they exist
        const chartIds = ['fcf-projection-chart', 'eps-projection-chart', 'ebitda-projection-chart', 'combined-projection-chart'];
        chartIds.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                const existingChart = Chart.getChart(canvas);
                if (existingChart) {
                    existingChart.destroy();
                }
            }
        });
        
        // Extract data for charts
        const years = projections.fcf_projections.map(item => item.year.toString());
        const fcfValues = projections.fcf_projections.map(item => item.value);
        const epsValues = projections.eps_projections.map(item => item.value);
        const ebitdaValues = projections.ebitda_projections.map(item => item.value);
        
        // Get current price for reference line
        const currentPrice = parseFloat(document.getElementById('current-price').textContent.replace(/[^0-9.-]+/g, ''));
        
        // Get form values for dynamic calculations
        const fcfYield = parseFloat(document.getElementById('fcf-yield').value) / 100;
        const epsMultiple = parseFloat(document.getElementById('eps-multiple').value);
        
        // Calculate projected prices based on FCF yield and EPS multiple
        const fcfPrices = fcfValues.map(fcf => fcf / fcfYield);
        const epsPrices = epsValues.map(eps => eps * epsMultiple);
        
        // Create FCF Projection Chart
        const fcfCtx = document.getElementById('fcf-projection-chart');
        if (fcfCtx) {
            new Chart(fcfCtx, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [
                        {
                            label: 'FCF/Share',
                            data: fcfValues,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1,
                            fill: true,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Projected Price',
                            data: fcfPrices,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderDash: [5, 5],
                            tension: 0.1,
                            fill: false,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'FCF/Share Projection & Price'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.raw;
                                    if (label === 'FCF/Share') {
                                        return `${label}: ${formatCurrency(value)}`;
                                    } else if (label === 'Projected Price') {
                                        return `${label}: ${formatCurrency(value)}`;
                                    }
                                    return `${label}: ${value}`;
                                }
                            }
                        },
                        annotation: {
                            annotations: {
                                line1: {
                                    type: 'line',
                                    yMin: currentPrice,
                                    yMax: currentPrice,
                                    borderColor: 'rgb(75, 192, 192)',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    label: {
                                        content: `Current Price: ${formatCurrency(currentPrice)}`,
                                        enabled: true,
                                        position: 'start'
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'FCF/Share'
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        },
                        y1: {
                            beginAtZero: false,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Price'
                            },
                            grid: {
                                drawOnChartArea: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create EPS Projection Chart with similar dual-axis approach
        const epsCtx = document.getElementById('eps-projection-chart');
        if (epsCtx) {
            new Chart(epsCtx, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [
                        {
                            label: 'EPS',
                            data: epsValues,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            tension: 0.1,
                            fill: true,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Projected Price',
                            data: epsPrices,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            borderDash: [5, 5],
                            tension: 0.1,
                            fill: false,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'EPS Projection & Price'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.raw;
                                    if (label === 'EPS') {
                                        return `${label}: ${formatCurrency(value)}`;
                                    } else if (label === 'Projected Price') {
                                        return `${label}: ${formatCurrency(value)}`;
                                    }
                                    return `${label}: ${value}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'EPS'
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        },
                        y1: {
                            beginAtZero: false,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Price'
                            },
                            grid: {
                                drawOnChartArea: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create EBITDA Projection Chart
        const ebitdaCtx = document.getElementById('ebitda-projection-chart');
        if (ebitdaCtx) {
            new Chart(ebitdaCtx, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [{
                        label: 'EBITDA/Share',
                        data: ebitdaValues,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        backgroundColor: 'rgba(255, 159, 64, 0.2)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'EBITDA/Share Projection'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `EBITDA/Share: ${formatCurrency(context.raw)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create Combined Projection Chart
        const combinedCtx = document.getElementById('combined-projection-chart');
        if (combinedCtx) {
            new Chart(combinedCtx, {
                type: 'line',
                data: {
                    labels: years,
                    datasets: [
                        {
                            label: 'FCF/Share',
                            data: fcfValues,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            tension: 0.1
                        },
                        {
                            label: 'EPS',
                            data: epsValues,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            tension: 0.1
                        },
                        {
                            label: 'EBITDA/Share',
                            data: ebitdaValues,
                            borderColor: 'rgba(255, 159, 64, 1)',
                            backgroundColor: 'transparent',
                            borderWidth: 2,
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Combined Projections'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    return `${label}: ${formatCurrency(context.raw)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value, false, 0);
                                }
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Helper function to update projection tables
    function updateProjectionTable(tableId, data) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        table.innerHTML = '';
        
        // Create header row
        const headerRow = document.createElement('tr');
        headerRow.classList.add('table-light');
        headerRow.innerHTML = '<th>Year</th><th>Value</th><th>Growth</th>';
        table.appendChild(headerRow);
        
        // Add data rows
        data.forEach((item, index) => {
            const row = document.createElement('tr');
            const growthText = index > 0 ? formatPercentage(item.growth) : 'Base';
            
            row.innerHTML = `
                <td>${item.year}</td>
                <td>${formatCurrency(item.value)}</td>
                <td>${growthText}</td>
            `;
            
            table.appendChild(row);
        });
    }
    
    // Function to update sensitivity analysis tables
    function updateSensitivityAnalysis(sensitivity) {
        if (!sensitivity) return;
        
        // FCF Growth Sensitivity
        if (sensitivity.fcf_growth) {
            createSensitivityTable('fcf-growth-table', sensitivity.fcf_growth, 'FCF Growth Rate (%)', 'FCF Yield (%)');
        }
        
        // EPS Growth Sensitivity
        if (sensitivity.eps_growth) {
            createSensitivityTable('eps-growth-table', sensitivity.eps_growth, 'EPS Growth Rate (%)', 'Terminal P/E');
        }
        
        // FCF Yield Sensitivity
        if (sensitivity.fcf_yield) {
            createSensitivityTable('fcf-yield-table', sensitivity.fcf_yield, 'FCF Yield (%)', 'Growth Rate (%)');
        }
        
        // Terminal P/E Sensitivity
        if (sensitivity.terminal_pe) {
            createSensitivityTable('terminal-pe-table', sensitivity.terminal_pe, 'Terminal P/E', 'Growth Rate (%)');
        }
        
        // Discount Rate Sensitivity
        if (sensitivity.discount_rate) {
            createSensitivityTable('discount-rate-table', sensitivity.discount_rate, 'Discount Rate (%)', 'Growth Rate (%)');
        }
    }
    
    // Helper function to create sensitivity tables
    function createSensitivityTable(tableId, data, rowLabel, colLabel) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        table.innerHTML = '';
        table.classList.add('sensitivity-table');
        
        // Get unique row and column values
        const rowValues = Object.keys(data).sort((a, b) => parseFloat(a) - parseFloat(b));
        if (rowValues.length === 0) return;
        
        const colValues = Object.keys(data[rowValues[0]]).sort((a, b) => parseFloat(a) - parseFloat(b));
        
        // Create header row
        const headerRow = document.createElement('tr');
        headerRow.classList.add('table-light');
        headerRow.innerHTML = `<th>${rowLabel} \\ ${colLabel}</th>`;
        colValues.forEach(col => {
            headerRow.innerHTML += `<th>${col}</th>`;
        });
        table.appendChild(headerRow);
        
        // Create data rows
        rowValues.forEach(row => {
            const dataRow = document.createElement('tr');
            dataRow.innerHTML = `<th>${row}</th>`;
            
            colValues.forEach(col => {
                const value = data[row][col];
                dataRow.innerHTML += `<td>${formatCurrency(value)}</td>`;
            });
            
            table.appendChild(dataRow);
        });
    }
    
    // Helper function to apply color coding based on value
    function applyColorCoding(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        if (value > 0) {
            element.classList.add('positive-value');
            element.classList.remove('negative-value');
        } else {
            element.classList.add('negative-value');
            element.classList.remove('positive-value');
        }
    }
    
    // Helper function to format currency values
    function formatCurrency(value, isBillions = false, decimals = 2) {
        if (value === null || value === undefined) return 'N/A';
        
        const formatter = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
        
        if (isBillions) {
            return formatter.format(value / 1e9) + 'B';
        }
        
        return formatter.format(value);
    }
    
    // Helper function to format percentage values
    function formatPercentage(value) {
        if (value === null || value === undefined) return 'N/A';
        
        const formatter = new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        return formatter.format(value / 100);
    }
    
    // Helper function to format large numbers
    function formatNumber(value) {
        if (value === null || value === undefined) return 'N/A';
        
        if (value >= 1e9) {
            return (value / 1e9).toFixed(2) + 'B';
        } else if (value >= 1e6) {
            return (value / 1e6).toFixed(2) + 'M';
        } else if (value >= 1e3) {
            return (value / 1e3).toFixed(2) + 'K';
        }
        
        return value.toFixed(0);
    }
    
    // Function to create a price projection chart
    function createPriceProjectionChart(currentPrice, targetPrice, years) {
        const canvas = document.getElementById('price-projection-chart');
        if (!canvas) return;
        
        // Destroy existing chart if it exists
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }
        
        // Generate data points for the chart
        const labels = [];
        const priceData = [];
        
        const currentYear = new Date().getFullYear();
        const currentQuarter = Math.floor((new Date().getMonth() / 3)) + 1;
        
        // Start with current price
        labels.push(`Q${currentQuarter} ${currentYear}`);
        priceData.push(currentPrice);
        
        // Calculate quarterly growth rate (compound)
        const quarterlyGrowthRate = Math.pow((targetPrice / currentPrice), 1 / (years * 4)) - 1;
        
        // Generate quarterly data points
        for (let i = 1; i <= years * 4; i++) {
            const quarter = ((currentQuarter + i - 1) % 4) + 1;
            const year = currentYear + Math.floor((currentQuarter + i - 1) / 4);
            
            if (i % 4 === 0) { // Only show year labels for Q4
                labels.push(`Q${quarter} ${year}`);
            } else if (i === years * 4) { // Always show the final quarter
                labels.push(`Q${quarter} ${year}`);
            } else {
                labels.push(`Q${quarter}`);
            }
            
            const projectedPrice = currentPrice * Math.pow(1 + quarterlyGrowthRate, i);
            priceData.push(projectedPrice);
        }
        
        // Create the chart
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Projected Price',
                    data: priceData,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Price: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value, false, 0);
                            }
                        }
                    },
                    x: {
                        display: true,
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 8
                        }
                    }
                }
            }
        });
    }
    
    // Run initial valuation for default symbol
    form.dispatchEvent(new Event('submit'));
}); 