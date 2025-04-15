document.addEventListener('DOMContentLoaded', function() {
    // Get form elements
    const stockSymbol = document.getElementById('stockSymbol');
    const searchBtn = document.getElementById('searchBtn');
    const calculateBtn = document.getElementById('calculateBtn');
    const includeEvEbitda = document.getElementById('includeEvEbitda');
    const includeSensitivity = document.getElementById('includeSensitivity');
    const projectionYearsSelect = document.getElementById('projectionYearsSelect');
    const projectionYears = document.getElementById('projectionYears');
    const featuresBtn = document.getElementById('featuresBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const marketDataCard = document.getElementById('marketDataCard');
    const resultsContainer = document.getElementById('resultsContainer');
    const introCard = document.getElementById('introCard');
    const sensitivityAlert = document.getElementById('sensitivityAlert');
    const sensitivityContent = document.getElementById('sensitivityContent');
    
    // Weight inputs
    const fcfWeight = document.getElementById('fcfWeight');
    const fcfWeightRange = document.getElementById('fcfWeightRange');
    const epsWeight = document.getElementById('epsWeight');
    const epsWeightRange = document.getElementById('epsWeightRange');
    const evEbitdaWeight = document.getElementById('evEbitdaWeight');
    const evEbitdaWeightRange = document.getElementById('evEbitdaWeightRange');
    const totalWeight = document.getElementById('totalWeight');
    const totalWeightDisplay = document.getElementById('totalWeightDisplay');
    
    // Initialize modals
    const featuresModal = new bootstrap.Modal(document.getElementById('featuresModal'));

    // Event listeners
    searchBtn.addEventListener('click', function() {
        fetchStockData(stockSymbol.value);
    });

    stockSymbol.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchStockData(stockSymbol.value);
        }
    });

    calculateBtn.addEventListener('click', function() {
        calculateValuation();
    });

    includeSensitivity.addEventListener('change', function() {
        updateSensitivityVisibility();
    });

    projectionYearsSelect.addEventListener('change', function() {
        projectionYears.value = this.value;
    });

    featuresBtn.addEventListener('click', function() {
        featuresModal.show();
    });
    
    // Weight sliders
    fcfWeightRange.addEventListener('input', function() {
        fcfWeight.value = this.value;
        updateWeights();
    });
    
    epsWeightRange.addEventListener('input', function() {
        epsWeight.value = this.value;
        updateWeights();
    });
    
    evEbitdaWeightRange.addEventListener('input', function() {
        evEbitdaWeight.value = this.value;
        updateWeights();
    });
    
    fcfWeight.addEventListener('input', function() {
        fcfWeightRange.value = this.value;
        updateWeights();
    });
    
    epsWeight.addEventListener('input', function() {
        epsWeightRange.value = this.value;
        updateWeights();
    });
    
    evEbitdaWeight.addEventListener('input', function() {
        evEbitdaWeightRange.value = this.value;
        updateWeights();
    });
    
    includeEvEbitda.addEventListener('change', function() {
        updateWeights();
        evEbitdaWeightRange.disabled = !this.checked;
        evEbitdaWeight.disabled = !this.checked;
    });
    
    // Update sensitivity visibility
    function updateSensitivityVisibility() {
        if (includeSensitivity.checked) {
            sensitivityAlert.classList.add('d-none');
            sensitivityContent.classList.remove('d-none');
        } else {
            sensitivityAlert.classList.remove('d-none');
            sensitivityContent.classList.add('d-none');
        }
    }
    
    // Update weights and validate total
    function updateWeights() {
        const fcfVal = parseInt(fcfWeight.value) || 0;
        const epsVal = parseInt(epsWeight.value) || 0;
        const evVal = includeEvEbitda.checked ? (parseInt(evEbitdaWeight.value) || 0) : 0;
        
        const sum = fcfVal + epsVal + evVal;
        totalWeight.textContent = sum;
        
        if (sum !== 100) {
            totalWeightDisplay.classList.remove('alert-info');
            totalWeightDisplay.classList.add('alert-warning');
        } else {
            totalWeightDisplay.classList.remove('alert-warning');
            totalWeightDisplay.classList.add('alert-info');
        }
    }

    // Function to fetch stock data
    function fetchStockData(symbol) {
        if (!symbol) {
            showToast('Please enter a valid stock symbol', 'warning');
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.remove('d-none');
        introCard.classList.add('d-none');
        
        // Make API request to get stock data
        fetch('/api/market_data/' + symbol.toUpperCase())
            .then(response => {
                if (!response.ok) {
                    throw new Error(response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update UI with stock data
                updateMarketDataUI(data);
                
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                
                // Show market data card
                marketDataCard.classList.remove('d-none');
                
                // Enable calculate button
                calculateBtn.disabled = false;
                
                // Scroll to market data
                marketDataCard.scrollIntoView({ behavior: 'smooth' });
                
                showToast(`Data for ${symbol.toUpperCase()} loaded successfully`, 'success');
            })
            .catch(error => {
                console.error('Error fetching stock data:', error);
                showToast(`Error: ${error.message}`, 'danger');
                
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                
                // Show intro card again
                introCard.classList.remove('d-none');
            });
    }

    // Function to update market data UI
    function updateMarketDataUI(data) {
        document.getElementById('symbolHeader').textContent = `${data.symbol} Market Data`;
        document.getElementById('currentPrice').textContent = formatCurrency(data.price);
        document.getElementById('sharesOutstanding').textContent = formatNumber(data.sharesOutstanding) + ' shares';
        document.getElementById('fcf').textContent = formatCurrency(data.freeCashFlow);
        document.getElementById('netIncome').textContent = formatCurrency(data.netIncome);
        document.getElementById('ebitda').textContent = formatCurrency(data.ebitda);
        document.getElementById('fcfPerShare').textContent = formatCurrency(data.freeCashFlow / data.sharesOutstanding);
        document.getElementById('eps').textContent = formatCurrency(data.netIncome / data.sharesOutstanding);
        document.getElementById('peRatio').textContent = ((data.price / (data.netIncome / data.sharesOutstanding)) || 0).toFixed(2) + 'x';
        document.getElementById('netDebt').textContent = formatCurrency(data.totalDebt - data.cashAndEquivalents);

        // Create or update valuation history section
        if (data.valuation_history) {
            createValuationHistorySection(data.valuation_history);
        }
    }

    // Function to create valuation history section
    function createValuationHistorySection(historyData) {
        // Store the history data globally
        window.valuation_history = historyData;
        
        // Create container if it doesn't exist
        let container = document.getElementById('valuationHistoryContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'valuationHistoryContainer';
            container.className = 'card bg-dark text-white mb-4';
            
            container.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-0">
                            <i class="bi bi-clock-history"></i> Valuation History
                        </h5>
                    </div>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-light btn-sm" data-period="1Y">1Y</button>
                        <button type="button" class="btn btn-outline-light btn-sm" data-period="2Y">2Y</button>
                        <button type="button" class="btn btn-outline-light btn-sm" data-period="3Y">3Y</button>
                        <button type="button" class="btn btn-outline-light btn-sm active" data-period="5Y">5Y</button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="mb-4">
                                <h6 class="mb-3">
                                    <i class="bi bi-graph-up"></i> Backtest Conclusion
                                </h6>
                                <div class="backtest-stats">
                                    <div class="mb-2" id="historicalOvervaluation"></div>
                                    <div class="mb-2" id="currentValuation"></div>
                                </div>
                            </div>
                            <div class="mb-4">
                                <h6 class="mb-3">
                                    <i class="bi bi-arrow-up-right"></i> Intrinsic Value Growth
                                    <span id="ivGrowthBadge" class="badge ms-2"></span>
                                </h6>
                                <div id="ivGrowthStats"></div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <canvas id="valuation-history-chart" height="300"></canvas>
                        </div>
                    </div>
                </div>
            `;
            
            // Insert after market data card
            const marketDataCard = document.getElementById('marketDataCard');
            marketDataCard.parentNode.insertBefore(container, marketDataCard.nextSibling);
            
            // Add event listeners for period buttons
            container.querySelectorAll('.btn-group button').forEach(button => {
                button.addEventListener('click', (e) => {
                    // Update active button
                    container.querySelectorAll('.btn-group button').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    // Update graph for selected period
                    updateValuationHistoryGraph(e.target.dataset.period);
                });
            });
        }

        // Update historical stats
        document.getElementById('historicalOvervaluation').innerHTML = `
            Historical average: Price 
            <span style="color: ${historyData.average_overvaluation > 0 ? '#e63946' : '#4cc9a0'}">
                ${Math.abs(historyData.average_overvaluation).toFixed(1)}% ${historyData.average_overvaluation > 0 ? 'above' : 'below'}
            </span> historical fair value
        `;
        
        // Add debug logging
        console.log("Current price:", historyData.current_price);
        console.log("Current fair value:", historyData.current_fair_value);
        console.log("Current overvaluation:", historyData.current_overvaluation);
        
        document.getElementById('currentValuation').innerHTML = `
            Current price: 
            <span style="color: ${historyData.current_overvaluation > 0 ? '#e63946' : '#4cc9a0'}">
                ${Math.abs(historyData.current_overvaluation).toFixed(1)}% ${historyData.current_overvaluation > 0 ? 'above' : 'below'}
            </span> historical fair value
            <i class="bi bi-info-circle" title="Based on current price vs fair value calculation"></i>
        `;

        // Update IV growth stats
        const ivGrowth = historyData.iv_cagr;
        const ivGrowthBadge = document.getElementById('ivGrowthBadge');
        ivGrowthBadge.textContent = `${Math.abs(ivGrowth).toFixed(1)}%`;
        ivGrowthBadge.className = `badge ms-2 ${ivGrowth >= 15 ? 'bg-success' : ivGrowth >= 10 ? 'bg-info' : 'bg-warning'}`;
        
        document.getElementById('ivGrowthStats').innerHTML = `
            Over the past 5 years, the intrinsic value of ${historyData.symbol} shares has 
            ${ivGrowth >= 0 ? 'increased' : 'decreased'} by ${Math.abs(ivGrowth).toFixed(1)}% (CAGR ${ivGrowth.toFixed(1)}%).
        `;

        // Initialize graph with 5Y data after a short delay to ensure canvas is ready
        setTimeout(() => {
            updateValuationHistoryGraph('5Y');
        }, 100);
    }

    // Function to update valuation history graph
    function updateValuationHistoryGraph(period = '5Y') {
        // Get the canvas element
        const ctx = document.getElementById('valuation-history-chart').getContext('2d');
        
        // Clear any existing chart
        if (window.valuation_chart) {
            window.valuation_chart.destroy();
        }
        
        // Filter data based on selected period
        const periodDays = {
            '1Y': 252,
            '2Y': 504,
            '3Y': 756,
            '5Y': 1260
        };
        
        const days = periodDays[period] || 1260;  // Default to 5Y if invalid period
        
        // Get the last N days of data
        const dates = window.valuation_history.dates.slice(-days);
        const prices = window.valuation_history.prices.slice(-days);
        const intrinsicValues = window.valuation_history.intrinsic_values.slice(-days);
        
        // Aggregate data into weekly points to reduce noise
        const aggregatedData = aggregateWeeklyData(dates, prices, intrinsicValues);
        
        // Create the chart
        window.valuation_chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: aggregatedData.dates.map(date => {
                    const d = new Date(date);
                    return d.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
                }),
                datasets: [
                    {
                        label: 'Stock Price',
                        data: aggregatedData.prices,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    },
                    {
                        label: 'Combined Fair Value',
                        data: aggregatedData.intrinsicValues,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('en-US', { 
                                        style: 'currency', 
                                        currency: 'USD',
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        position: 'right',
                        grid: {
                            color: 'rgba(200, 200, 200, 0.2)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }

    function aggregateWeeklyData(dates, prices, intrinsicValues) {
        const weeklyData = {
            dates: [],
            prices: [],
            intrinsicValues: []
        };
        
        let currentWeek = [];
        let currentPrices = [];
        let currentIntrinsicValues = [];
        
        // Group data by week
        for (let i = 0; i < dates.length; i++) {
            const date = new Date(dates[i]);
            
            if (currentWeek.length === 0 || 
                new Date(currentWeek[0]).getWeek() === date.getWeek()) {
                currentWeek.push(dates[i]);
                currentPrices.push(prices[i]);
                currentIntrinsicValues.push(intrinsicValues[i]);
            } else {
                // Calculate weekly averages
                if (currentPrices.length > 0) {
                    weeklyData.dates.push(currentWeek[Math.floor(currentWeek.length / 2)]);
                    weeklyData.prices.push(
                        currentPrices.reduce((a, b) => a + b, 0) / currentPrices.length
                    );
                    weeklyData.intrinsicValues.push(
                        currentIntrinsicValues.reduce((a, b) => a + b, 0) / currentIntrinsicValues.length
                    );
                }
                
                // Start new week
                currentWeek = [dates[i]];
                currentPrices = [prices[i]];
                currentIntrinsicValues = [intrinsicValues[i]];
            }
        }
        
        // Add the last week if not empty
        if (currentPrices.length > 0) {
            weeklyData.dates.push(currentWeek[Math.floor(currentWeek.length / 2)]);
            weeklyData.prices.push(
                currentPrices.reduce((a, b) => a + b, 0) / currentPrices.length
            );
            weeklyData.intrinsicValues.push(
                currentIntrinsicValues.reduce((a, b) => a + b, 0) / currentIntrinsicValues.length
            );
        }
        
        return weeklyData;
    }

    // Helper function to get week number
    Date.prototype.getWeek = function() {
        const d = new Date(Date.UTC(this.getFullYear(), this.getMonth(), this.getDate()));
        const dayNum = d.getUTCDay() || 7;
        d.setUTCDate(d.getUTCDate() + 4 - dayNum);
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
        return Math.ceil((((d - yearStart) / 86400000) + 1)/7);
    };

    // Function to calculate valuation
    function calculateValuation() {
        // Get form values
        const symbol = stockSymbol.value;
        const fcfGrowth = parseFloat(document.getElementById('fcfGrowth').value);
        const epsGrowth = parseFloat(document.getElementById('epsGrowth').value);
        const ebitdaGrowth = parseFloat(document.getElementById('ebitdaGrowth').value);
        const fcfYield = parseFloat(document.getElementById('fcfYield').value);
        const terminalPE = parseFloat(document.getElementById('terminalPE').value);
        const epsMultiple = parseFloat(document.getElementById('epsMultiple').value);
        const years = parseInt(document.getElementById('calculationYears').value);
        const projectionYearsVal = parseInt(projectionYears.value);
        const sbcImpact = parseFloat(document.getElementById('sbcImpact').value);
        const fcfWeightVal = parseFloat(fcfWeight.value) / 100;
        const epsWeightVal = parseFloat(epsWeight.value) / 100;
        const evEbitdaWeightVal = parseFloat(evEbitdaWeight.value) / 100;
        const useEvEbitda = includeEvEbitda.checked;
        const sensitivity = includeSensitivity.checked;

        // Validate form values
        if (!symbol) {
            showToast('Please enter a valid stock symbol', 'warning');
            return;
        }
        
        const totalWeightCheck = (fcfWeightVal + epsWeightVal + (useEvEbitda ? evEbitdaWeightVal : 0)) * 100;
        if (Math.round(totalWeightCheck) !== 100) {
            showToast('Model weights must sum to 100%', 'warning');
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.remove('d-none');
        
        // Update status indicators
        document.querySelectorAll('.status-indicator').forEach(indicator => {
            indicator.style.backgroundColor = '#ffc107';
        });

        // Create request body
        const requestBody = {
            symbol: symbol,
            fcf_growth: fcfGrowth,
            eps_growth: epsGrowth,
            ebitda_growth: ebitdaGrowth,
            fcf_yield: fcfYield,
            terminal_pe: terminalPE,
            eps_multiple: epsMultiple,
            years: years,
            projection_years: projectionYearsVal,
            sbc_impact: sbcImpact,
            fcf_weight: fcfWeightVal * 100,
            eps_weight: epsWeightVal * 100,
            ev_ebitda_weight: evEbitdaWeightVal * 100,
            use_ev_ebitda: useEvEbitda,
            sensitivity: sensitivity
        };

        // Make API request to calculate valuation
        fetch('/api/valuation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                
                // Show results container
                resultsContainer.classList.remove('d-none');
                
                // Update UI with valuation results
                updateValuationUI(data);
                
                // Scroll to results
                resultsContainer.scrollIntoView({ behavior: 'smooth' });
                
                showToast('Valuation calculated successfully', 'success');
            })
            .catch(error => {
                console.error('Error calculating valuation:', error);
                showToast('Error calculating valuation. Please try again.', 'danger');
                
                // Hide loading overlay
                loadingOverlay.classList.add('d-none');
                
                // Update status indicators
                document.querySelectorAll('.status-indicator').forEach(indicator => {
                    indicator.style.backgroundColor = '#dc3545';
                });
            });
    }

    // Function to format return value with status text
    function formatReturnWithStatus(returnValue) {
        const absoluteValue = Math.abs(returnValue);
        const formattedValue = formatPercentage(absoluteValue);
        
        if (returnValue > 0) {
            return {
                text: 'Undervalued by',
                value: formattedValue,
                color: '#4cc9a0' // Green for undervalued
            };
        } else if (returnValue < 0) {
            return {
                text: 'Overvalued by',
                value: formattedValue,
                color: '#e63946' // Red for overvalued
            };
        } else {
            return {
                text: 'Fairly valued',
                value: '0%',
                color: '#ffba08' // Yellow for fair value
            };
        }
    }

    // Function to update valuation UI
    function updateValuationUI(data) {
        // Update valuation results table
        const currentPrice = data.market_data.current_price;
        const fcfValue = data.valuation_results.fcf_based;
        const epsValue = data.valuation_results.eps_based;
        const evEbitdaValue = data.valuation_results.ev_ebitda_based;
        const weightedValue = data.valuation_results.weighted_average;
        const upsidePotential = data.valuation_results.upside_potential;

        document.getElementById('fcfValue').textContent = formatCurrency(fcfValue);
        document.getElementById('epsValue').textContent = formatCurrency(epsValue);
        document.getElementById('evEbitdaValue').textContent = formatCurrency(evEbitdaValue);
        document.getElementById('weightedValue').textContent = formatCurrency(weightedValue);

        const fcfReturn = (fcfValue / currentPrice - 1) * 100;
        const epsReturn = (epsValue / currentPrice - 1) * 100;
        const evEbitdaReturn = (evEbitdaValue / currentPrice - 1) * 100;
        
        // Update return values with status text
        updateReturnCell('fcfReturn', fcfReturn);
        updateReturnCell('epsReturn', epsReturn);
        updateReturnCell('evEbitdaReturn', evEbitdaReturn);
        updateReturnCell('weightedReturn', upsidePotential);

        // Set status indicators
        setStatusColor('fcfRow', fcfReturn);
        setStatusColor('epsRow', epsReturn);
        setStatusColor('evEbitdaRow', evEbitdaReturn);
        setStatusColor('weightedRow', upsidePotential);

        // Toggle EV/EBITDA row visibility
        document.getElementById('evEbitdaRow').style.display = includeEvEbitda.checked ? '' : 'none';

        // Update WACC components if they exist
        if (data.wacc_components) {
            document.getElementById('betaValue').textContent = data.wacc_components.beta.toFixed(2);
            document.getElementById('riskFreeRateValue').textContent = formatPercentage(data.wacc_components.risk_free_rate * 100);
            document.getElementById('debtToEquityValue').textContent = data.wacc_components.debt_to_equity ? data.wacc_components.debt_to_equity.toFixed(2) : 'N/A';
            document.getElementById('costOfDebtValue').textContent = data.wacc_components.cost_of_debt ? formatPercentage(data.wacc_components.cost_of_debt * 100) : 'N/A';
            document.getElementById('calculatedWaccValue').textContent = formatPercentage(data.wacc_components.calculated_wacc * 100);
        }

        // Update projections
        updateProjections(data.projections);

        // Update valuation history if available
        if (data.valuation_history) {
            updateValuationHistory(data.valuation_history);
        }
        
        // Update sensitivity analysis if included
        if (includeSensitivity.checked && data.sensitivity_analysis) {
            updateSensitivityAnalysis(data.sensitivity_analysis);
        }
        
        // Update sensitivity visibility
        updateSensitivityVisibility();
    }
    
    // Helper function to update return cell
    function updateReturnCell(cellId, returnValue) {
        const cell = document.getElementById(cellId);
        const formattedReturn = formatReturnWithStatus(returnValue);
        
        cell.querySelector('.status-text').textContent = formattedReturn.text;
        cell.querySelector('.return-value').textContent = formattedReturn.value;
        cell.style.color = formattedReturn.color;
    }
    
    // Set status indicator color based on return
    function setStatusColor(rowId, returnValue) {
        const indicator = document.querySelector(`#${rowId} .status-indicator`);
        
        if (returnValue >= 20) {
            indicator.style.backgroundColor = '#4cc9a0'; // success
        } else if (returnValue > 0) {
            indicator.style.backgroundColor = '#ffba08'; // warning
        } else {
            indicator.style.backgroundColor = '#e63946'; // danger
        }
    }

    // Function to update projections
    function updateProjections(projections) {
        // Update FCF projections table
        const fcfTable = document.getElementById('fcfProjectionsTable').getElementsByTagName('tbody')[0];
        fcfTable.innerHTML = '';
        projections.fcf.forEach(item => {
            const row = fcfTable.insertRow();
            row.insertCell(0).textContent = item.year;
            row.insertCell(1).textContent = formatCurrency(item.value);
            
            const growthCell = row.insertCell(2);
            growthCell.textContent = formatPercentage(item.growth);
            growthCell.style.color = item.growth >= 0 ? '#4cc9a0' : '#e63946';
        });

        // Update EPS projections table
        const epsTable = document.getElementById('epsProjectionsTable').getElementsByTagName('tbody')[0];
        epsTable.innerHTML = '';
        projections.eps.forEach(item => {
            const row = epsTable.insertRow();
            row.insertCell(0).textContent = item.year;
            row.insertCell(1).textContent = formatCurrency(item.value);
            
            const growthCell = row.insertCell(2);
            growthCell.textContent = formatPercentage(item.growth);
            growthCell.style.color = item.growth >= 0 ? '#4cc9a0' : '#e63946';
        });

        // Update EBITDA projections table
        const ebitdaTable = document.getElementById('ebitdaProjectionsTable').getElementsByTagName('tbody')[0];
        ebitdaTable.innerHTML = '';
        if (projections.ebitda) {
            projections.ebitda.forEach(item => {
                const row = ebitdaTable.insertRow();
                row.insertCell(0).textContent = item.year;
                row.insertCell(1).textContent = formatCurrency(item.value);
                
                const growthCell = row.insertCell(2);
                growthCell.textContent = formatPercentage(item.growth);
                growthCell.style.color = item.growth >= 0 ? '#4cc9a0' : '#e63946';
            });
        }

        // Create projection graphs
        createProjectionGraphs(projections);
    }

    // Function to create projection graphs
    function createProjectionGraphs(projections) {
        // Destroy existing charts if they exist
        const existingFcfChart = Chart.getChart('fcfProjectionGraph');
        const existingEpsChart = Chart.getChart('epsProjectionGraph');
        if (existingFcfChart) existingFcfChart.destroy();
        if (existingEpsChart) existingEpsChart.destroy();

        // FCF projection graph
        const fcfYears = projections.fcf.map(item => item.year);
        const fcfValues = projections.fcf.map(item => item.value);

        const fcfChart = new Chart(document.getElementById('fcfProjectionGraph'), {
            type: 'line',
            data: {
                labels: fcfYears,
                datasets: [{
                    label: 'FCF/Share',
                    data: fcfValues,
                    borderColor: '#4cc9a0',
                    backgroundColor: '#4cc9a0',
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'FCF/Share Projections',
                        color: '#f8f9fa',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#2b2d42',
                        titleColor: '#f8f9fa',
                        bodyColor: '#f8f9fa',
                        callbacks: {
                            label: function(context) {
                                return `FCF/Share: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa'
                        },
                        title: {
                            display: true,
                            text: 'Year',
                            color: '#f8f9fa'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa',
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Value ($)',
                            color: '#f8f9fa'
                        }
                    }
                }
            }
        });

        // EPS projection graph
        const epsYears = projections.eps.map(item => item.year);
        const epsValues = projections.eps.map(item => item.value);

        const epsChart = new Chart(document.getElementById('epsProjectionGraph'), {
            type: 'line',
            data: {
                labels: epsYears,
                datasets: [{
                    label: 'EPS',
                    data: epsValues,
                    borderColor: '#4895ef',
                    backgroundColor: '#4895ef',
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'EPS Projections',
                        color: '#f8f9fa',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#2b2d42',
                        titleColor: '#f8f9fa',
                        bodyColor: '#f8f9fa',
                        callbacks: {
                            label: function(context) {
                                return `EPS: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa'
                        },
                        title: {
                            display: true,
                            text: 'Year',
                            color: '#f8f9fa'
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: {
                            color: '#f8f9fa',
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        },
                        title: {
                            display: true,
                            text: 'Value ($)',
                            color: '#f8f9fa'
                        }
                    }
                }
            }
        });

        // Add window resize handler
        window.addEventListener('resize', function() {
            fcfChart.resize();
            epsChart.resize();
        });
    }

    // Function to update sensitivity analysis
    function updateSensitivityAnalysis(sensitivityData) {
        // FCF Growth sensitivity
        createSensitivityTable('fcfGrowthSensitivityTable', sensitivityData.fcf_growth, 'Growth Rate (%)', 'FCF Yield (%)');

        // EPS Growth sensitivity
        createSensitivityTable('epsGrowthSensitivityTable', sensitivityData.eps_growth, 'Growth Rate (%)', 'P/E Multiple');

        // WACC sensitivity
        if (sensitivityData.wacc) {
            createSensitivityTable('waccSensitivityTable', sensitivityData.wacc, 'Beta', 'Risk-Free Rate (%)', true);
        }
    }

    // Function to create sensitivity tables
    function createSensitivityTable(tableId, data, rowLabel, colLabel, isPercentage = false) {
        const table = document.getElementById(tableId);
        table.innerHTML = '';

        // Remove any existing explanation divs
        const existingExplanations = table.parentNode.querySelectorAll('.sensitivity-explanation');
        existingExplanations.forEach(div => div.remove());
        
        // Add explanation div above table
        const explanationDiv = document.createElement('div');
        explanationDiv.className = 'sensitivity-explanation mb-3 p-3 rounded';
        explanationDiv.style.backgroundColor = 'rgba(255,255,255,0.1)';
        explanationDiv.style.color = '#f8f9fa';
        
        if (tableId === 'fcfGrowthSensitivityTable') {
            explanationDiv.innerHTML = `
                <h6 class="mb-2"><i class="bi bi-info-circle"></i> FCF Growth Sensitivity</h6>
                <p class="mb-0" style="font-size: 0.9rem">
                    This table shows how different combinations of FCF Growth Rate and FCF Yield affect the stock's intrinsic value.
                    <ul class="mt-2 mb-0">
                        <li>Higher growth rates typically justify higher valuations</li>
                        <li>Lower FCF yields suggest higher valuation multiples</li>
                        <li>Green cells indicate potentially undervalued scenarios</li>
                        <li>Red cells indicate potentially overvalued scenarios</li>
                    </ul>
                </p>`;
        } else if (tableId === 'epsGrowthSensitivityTable') {
            explanationDiv.innerHTML = `
                <h6 class="mb-2"><i class="bi bi-info-circle"></i> EPS Growth Sensitivity</h6>
                <p class="mb-0" style="font-size: 0.9rem">
                    This table demonstrates how EPS Growth Rate and P/E Multiple combinations impact valuation.
                    <ul class="mt-2 mb-0">
                        <li>Higher growth rates typically command higher P/E multiples</li>
                        <li>Industry average P/E is used as a baseline</li>
                        <li>Green cells suggest attractive growth-to-multiple scenarios</li>
                        <li>Red cells indicate potentially expensive valuations</li>
                    </ul>
                </p>`;
        } else if (tableId === 'waccSensitivityTable') {
            explanationDiv.innerHTML = `
                <h6 class="mb-2"><i class="bi bi-info-circle"></i> WACC Analysis</h6>
                <p class="mb-0" style="font-size: 0.9rem">
                    This table shows how Beta and Risk-Free Rate affect the Weighted Average Cost of Capital (WACC).
                    <ul class="mt-2 mb-0">
                        <li>Lower WACC (green) generally leads to higher valuations</li>
                        <li>Higher Beta indicates more market sensitivity</li>
                        <li>Risk-free rate based on 10-year Treasury yield</li>
                        <li>Industry average Beta is used as reference</li>
                    </ul>
                </p>`;
        }
        
        table.parentNode.insertBefore(explanationDiv, table);

        // Get row and column headers
        const rowKeys = Object.keys(data).sort((a, b) => parseFloat(a) - parseFloat(b));
        const colKeys = Object.keys(data[rowKeys[0]]).sort((a, b) => parseFloat(a) - parseFloat(b));

        // Create header row
        const headerRow = table.insertRow();
        const headerCell = headerRow.insertCell();
        headerCell.textContent = `${rowLabel} \\ ${colLabel}`;
        headerCell.style.fontWeight = '600';
        headerCell.style.backgroundColor = 'rgba(0,0,0,0.2)';
        headerCell.style.color = '#f8f9fa';
        
        colKeys.forEach(colKey => {
            const cell = headerRow.insertCell();
            cell.textContent = colKey;
            cell.style.fontWeight = '600';
            cell.style.backgroundColor = 'rgba(0,0,0,0.2)';
            cell.style.color = '#f8f9fa';
        });

        // Create data rows
        rowKeys.forEach(rowKey => {
            const row = table.insertRow();
            const headerCell = row.insertCell();
            headerCell.textContent = rowKey;
            headerCell.style.fontWeight = '600';
            headerCell.style.backgroundColor = 'rgba(0,0,0,0.2)';
            headerCell.style.color = '#f8f9fa';
            
            colKeys.forEach(colKey => {
                const value = data[rowKey][colKey];
                const cell = row.insertCell();
                cell.textContent = isPercentage ? formatPercentage(value) : formatCurrency(value);
                
                // Enhanced cell styling with better contrast
                if (!isPercentage && value > 0) {
                    const currentPrice = parseFloat(document.getElementById('currentPrice').textContent.replace(/[^0-9.-]+/g, ''));
                    const upside = value / currentPrice - 1;
                    
                    if (upside > 0.3) {
                        cell.style.backgroundColor = '#4cc9a0';
                        cell.style.color = '#000000';
                        cell.title = `Strong Buy: ${formatPercentage(upside * 100)} potential upside`;
                    } else if (upside > 0) {
                        cell.style.backgroundColor = '#90be6d';
                        cell.style.color = '#000000';
                        cell.title = `Moderate Buy: ${formatPercentage(upside * 100)} potential upside`;
                    } else {
                        cell.style.backgroundColor = '#e63946';
                        cell.style.color = '#ffffff';
                        cell.title = `Overvalued: ${formatPercentage(Math.abs(upside * 100))} potential downside`;
                    }
                } else if (isPercentage) {
                    // For WACC, lower values are generally better
                    const val = parseFloat(value);
                    if (val < 8) {
                        cell.style.backgroundColor = '#4cc9a0';
                        cell.style.color = '#000000';
                        cell.title = 'Low WACC: Favorable for valuation';
                    } else if (val < 10) {
                        cell.style.backgroundColor = '#ffba08';
                        cell.style.color = '#000000';
                        cell.title = 'Moderate WACC: Neutral for valuation';
                    } else {
                        cell.style.backgroundColor = '#e63946';
                        cell.style.color = '#ffffff';
                        cell.title = 'High WACC: May reduce valuation';
                    }
                }
                
                // Add hover effect
                cell.style.cursor = 'help';
                cell.style.transition = 'opacity 0.2s';
                cell.addEventListener('mouseover', () => cell.style.opacity = '0.8');
                cell.addEventListener('mouseout', () => cell.style.opacity = '1');
            });
        });
    }
    
    // Show toast notification
    function showToast(message, type) {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.innerHTML += toastHtml;
        
        // Initialize and show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            animation: true,
            autohide: true,
            delay: 3000
        });
        toast.show();
        
        // Remove toast after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }

    // Helper function to format currency
    function formatCurrency(value) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    }

    // Helper function to format percentage
    function formatPercentage(value) {
        return value.toFixed(2) + '%';
    }

    // Helper function to format large numbers
    function formatNumber(value) {
        if (value >= 1000000000) {
            return (value / 1000000000).toFixed(2) + 'B';
        } else if (value >= 1000000) {
            return (value / 1000000).toFixed(2) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(2) + 'K';
        } else {
            return value.toFixed(2);
        }
    }
    
    // Initialize weights and sensitivity visibility
    updateWeights();
    updateSensitivityVisibility();
}); 