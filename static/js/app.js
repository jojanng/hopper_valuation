document.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-target');
            
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding content
            tab.classList.add('active');
            document.getElementById(target).classList.add('active');
        });
    });
    
    // Stock data fetching
    const symbolInput = document.getElementById('symbol');
    const fetchDataBtn = document.getElementById('fetch-data-btn');
    const stockResultSection = document.getElementById('stock-result');
    const errorMessage = document.getElementById('error-message');
    const loadingIndicator = document.getElementById('loading');
    
    fetchDataBtn.addEventListener('click', async () => {
        await fetchStockData();
    });
    
    symbolInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            fetchStockData();
        }
    });
    
    // Model selection
    const modelBtns = document.querySelectorAll('.model-btn');
    const pricingSection = document.getElementById('pricing-section');
    const pricingTitle = document.getElementById('pricing-title');
    const strikeGroup = document.getElementById('strike-group');
    const fcfGroup = document.getElementById('fcf-group');
    const pricingResultSection = document.getElementById('pricing-result');
    
    let selectedModel = null;
    
    modelBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const model = btn.getAttribute('data-model');
            selectedModel = model;
            
            // Remove active class from all model buttons
            modelBtns.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Reset pricing result section
            pricingResultSection.style.display = 'none';
            pricingResultSection.classList.remove('visible');
            
            // Clear any previous chart
            if (window.valuationChart) {
                window.valuationChart.destroy();
                window.valuationChart = null;
            }
            
            // Clear any previous results
            document.getElementById('pricing-data-grid').innerHTML = '';
            document.getElementById('valuation-summary').style.display = 'none';
            document.getElementById('valuation-chart').style.display = 'none';
            
            // Update tabs based on selected model
            updateTabsForModel(model);
            
            // Show pricing section
            pricingSection.style.display = 'block';
            
            // Update title based on selected model
            pricingTitle.innerText = model === 'options' ? 'Options Pricing' : 'Stock Valuation';
            
            // Show/hide strike price input for options
            strikeGroup.style.display = model === 'options' ? 'block' : 'none';
            
            // Show/hide FCF input for stocks
            fcfGroup.style.display = model === 'stocks' ? 'block' : 'none';
            
            // Animate the pricing section appearance
            setTimeout(() => {
                pricingSection.classList.add('visible');
            }, 100);
        });
    });
    
    // Function to update tabs based on selected model
    function updateTabsForModel(model) {
        const tabsContainer = document.querySelector('.tabs');
        
        // Clear existing tabs and content
        tabsContainer.innerHTML = '';
        
        // Hide all tab contents first
        document.querySelectorAll('.tab-content').forEach(content => {
            content.style.display = 'none';
            content.classList.remove('active');
        });
        
        if (model === 'options') {
            // Options model tabs
            tabsContainer.innerHTML = `
                <div class="tab active" data-target="tab-options">Options Analysis</div>
                <div class="tab" data-target="tab-fft-algorithm">FFT Algorithm</div>
            `;
            
            // Create options tab content if it doesn't exist
            if (!document.getElementById('tab-options')) {
                const optionsTab = document.createElement('div');
                optionsTab.id = 'tab-options';
                optionsTab.className = 'tab-content active';
                optionsTab.innerHTML = `
                    <h3>About Options Analysis</h3>
                    <p>Our options analysis uses the Black-Scholes model to calculate probabilities for options at expiration:</p>
                    <ul>
                        <li><strong>Call Options</strong> - Probability that the stock price will be above the strike price at expiration.</li>
                        <li><strong>Put Options</strong> - Probability that the stock price will be below the strike price at expiration.</li>
                    </ul>
                    <p>These probabilities are based on the current price, strike price, time to maturity, and historical volatility.</p>
                `;
                document.getElementById('pricing-result').appendChild(optionsTab);
            } else {
                document.getElementById('tab-options').style.display = 'block';
                document.getElementById('tab-options').classList.add('active');
            }
            
            // Create FFT algorithm tab content if it doesn't exist
            if (!document.getElementById('tab-fft-algorithm')) {
                const fftTab = document.createElement('div');
                fftTab.id = 'tab-fft-algorithm';
                fftTab.className = 'tab-content';
                fftTab.style.display = 'none';
                fftTab.innerHTML = `
                    <h3>Fast Fourier Transform (FFT) Algorithm</h3>
                    <p>Our options pricing model uses the Fast Fourier Transform (FFT) method to efficiently calculate option prices:</p>
                    <ul>
                        <li><strong>Characteristic Function</strong> - We use the characteristic function of the log-price to represent the probability distribution.</li>
                        <li><strong>FFT Algorithm</strong> - The FFT algorithm efficiently transforms the characteristic function to option prices for multiple strikes.</li>
                        <li><strong>Risk-Neutral Valuation</strong> - Prices are calculated under the risk-neutral measure, ensuring no-arbitrage conditions.</li>
                    </ul>
                    <p>This approach is particularly powerful for handling complex price dynamics and is more computationally efficient than traditional methods.</p>
                `;
                document.getElementById('pricing-result').appendChild(fftTab);
            } else {
                document.getElementById('tab-fft-algorithm').style.display = 'none';
                document.getElementById('tab-fft-algorithm').classList.remove('active');
            }
            
        } else {
            // Stock valuation model tabs
            tabsContainer.innerHTML = `
                <div class="tab active" data-target="tab-valuation">Valuation</div>
                <div class="tab" data-target="tab-methodology">Methodology</div>
            `;
            
            // Show only the active tab content
            document.getElementById('tab-valuation').style.display = 'block';
            document.getElementById('tab-valuation').classList.add('active');
            document.getElementById('tab-methodology').style.display = 'none';
            document.getElementById('tab-methodology').classList.remove('active');
            
            // Hide options tabs if they exist
            if (document.getElementById('tab-options')) {
                document.getElementById('tab-options').style.display = 'none';
                document.getElementById('tab-options').classList.remove('active');
            }
            if (document.getElementById('tab-fft-algorithm')) {
                document.getElementById('tab-fft-algorithm').style.display = 'none';
                document.getElementById('tab-fft-algorithm').classList.remove('active');
            }
        }
        
        // Add event listeners to new tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.getAttribute('data-target');
                
                // Remove active class from all tabs and hide all contents
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                    content.style.display = 'none';
                });
                
                // Add active class to clicked tab and show corresponding content
                tab.classList.add('active');
                const targetContent = document.getElementById(target);
                if (targetContent) {
                    targetContent.classList.add('active');
                    targetContent.style.display = 'block';
                }
            });
        });
    }
    
    // FCF input handling
    const fcfInput = document.getElementById('fcf-input');
    const fcfUpdateBtn = document.getElementById('fcf-update-btn');
    
    fcfUpdateBtn.addEventListener('click', async () => {
        const symbol = symbolInput.value.trim();
        const fcfValue = fcfInput.value.trim();
        
        if (!symbol || !fcfValue) {
            showError("Please enter both a stock symbol and FCF value");
            return;
        }
        
        try {
            const response = await fetch('/set-fcf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    symbol: symbol,
                    fcf_value: parseFloat(fcfValue)
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
            } else {
                // Show success message
                const successMsg = document.createElement('div');
                successMsg.className = 'success-message';
                successMsg.textContent = data.message;
                fcfGroup.appendChild(successMsg);
                
                // Remove after 3 seconds
                setTimeout(() => {
                    successMsg.remove();
                }, 3000);
            }
        } catch (error) {
            showError("Failed to update FCF value. Please try again.");
            console.error(error);
        }
    });
    
    // Pricing calculation
    const calculateBtn = document.getElementById('calculate-btn');
    
    calculateBtn.addEventListener('click', async () => {
        await fetchPricing();
    });
    
    // Function to fetch stock data
    async function fetchStockData() {
        const symbol = symbolInput.value.trim();
        
        if (!symbol) {
            showError("Please enter a stock symbol");
            return;
        }
        
        showLoading(true);
        hideError();
        
        try {
            const response = await fetch(`/stock-data?symbol=${symbol}`);
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
            } else {
                displayStockData(data);
                stockResultSection.classList.add('visible');
                
                // Set FCF input value if available
                if (data.annual_fcf) {
                    fcfInput.value = data.annual_fcf.toFixed(2);
                }
            }
        } catch (error) {
            showError("Failed to fetch stock data. Please try again.");
            console.error(error);
        } finally {
            showLoading(false);
        }
    }
    
    // Function to fetch pricing data
    async function fetchPricing() {
        const symbol = symbolInput.value.trim();
        const maturity = document.getElementById('maturity').value;
        let strike = null;
        
        if (selectedModel === 'options') {
            strike = document.getElementById('strike').value;
            if (!strike) {
                showError("Please enter a strike price for options pricing");
                return;
            }
        }
        
        if (!symbol || !maturity) {
            showError("Please enter all required fields");
            return;
        }
        
        showLoading(true);
        hideError();
        
        try {
            let requestUrl = `/pricing?symbol=${symbol}&model_type=${selectedModel}&time_to_maturity=${maturity}`;
            if (strike) requestUrl += `&strike_price=${strike}`;
            
            console.log("Fetching pricing data from:", requestUrl);
            
            const response = await fetch(requestUrl);
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                console.error("API error:", data.error);
            } else {
                console.log("Received pricing data:", data);
                
                // Make sure pricing result section is visible
                pricingResultSection.style.display = 'block';
                
                // Update tabs based on selected model
                updateTabsForModel(selectedModel);
                
                // Display the data
                displayPricingData(data);
                
                // Add visible class for animation
                setTimeout(() => {
                    pricingResultSection.classList.add('visible');
                }, 100);
                
                // If we have chart data and it's stock valuation, render the chart
                if (selectedModel === 'stocks' && data.intrinsic_value_per_share) {
                    renderValuationChart(data);
                }
            }
        } catch (error) {
            showError("Failed to calculate pricing. Please try again.");
            console.error("Fetch error:", error);
        } finally {
            showLoading(false);
        }
    }
    
    // Function to display stock data
    function displayStockData(data) {
        const stockDataGrid = document.getElementById('stock-data-grid');
        
        stockDataGrid.innerHTML = `
            <div class="data-item">
                <h4>Current Price</h4>
                <p>$${data.current_price.toFixed(2)}</p>
            </div>
            <div class="data-item">
                <h4>Historical Volatility</h4>
                <p>${(data.historical_volatility * 100).toFixed(1)}%</p>
            </div>
            <div class="data-item">
                <h4>Risk-Free Rate</h4>
                <p>${(data.risk_free_rate * 100).toFixed(1)}%</p>
            </div>
            <div class="data-item">
                <h4>Dividend Yield</h4>
                <p>${(data.dividend_yield * 100).toFixed(1)}%</p>
            </div>
            ${data.annual_fcf ? `
            <div class="data-item">
                <h4>Annual FCF</h4>
                <p>$${data.annual_fcf.toFixed(2)}B</p>
            </div>
            ` : ''}
        `;
        
        // Enable model selection buttons
        document.querySelectorAll('.model-btn').forEach(btn => {
            btn.disabled = false;
        });
    }
    
    // Function to display pricing data
    function displayPricingData(data) {
        const pricingDataGrid = document.getElementById('pricing-data-grid');
        
        // Remove any existing options explanation
        const existingExplanation = document.querySelector('.options-explanation');
        if (existingExplanation) {
            existingExplanation.remove();
        }
        
        if (selectedModel === 'options') {
            console.log("Displaying options pricing data:", data);
            
            // Format probabilities
            const callProbability = data.probability_above_strike ? (data.probability_above_strike * 100).toFixed(2) : 'N/A';
            const putProbability = data.probability_below_strike ? (data.probability_below_strike * 100).toFixed(2) : 'N/A';
            
            // Check if strike price is reasonable compared to current price
            const currentPrice = data.current_price;
            const strikePrice = data.strike_price;
            const strikePriceRatio = strikePrice / currentPrice;
            
            // Determine if the strike price is reasonable (within 50% of current price)
            const isReasonableStrike = strikePriceRatio >= 0.5 && strikePriceRatio <= 1.5;
            
            pricingDataGrid.innerHTML = `
                <div class="data-item">
                    <h4>Current Price</h4>
                    <p>$${data.current_price ? data.current_price.toFixed(2) : 'N/A'}</p>
                </div>
                <div class="data-item">
                    <h4>Strike Price</h4>
                    <p>$${data.strike_price ? data.strike_price.toFixed(2) : 'N/A'}</p>
                </div>
                <div class="data-item">
                    <h4>Expected Future Price</h4>
                    <p>$${data.expected_price ? data.expected_price.toFixed(2) : 'N/A'}</p>
                </div>
                <div class="data-item ${isReasonableStrike ? '' : 'warning'}">
                    <h4>Call Option Probability</h4>
                    <p>${isReasonableStrike ? callProbability + '%' : 'See note below'}</p>
                </div>
                <div class="data-item ${isReasonableStrike ? '' : 'warning'}">
                    <h4>Put Option Probability</h4>
                    <p>${isReasonableStrike ? putProbability + '%' : 'See note below'}</p>
                </div>
                <div class="data-item">
                    <h4>Time to Maturity</h4>
                    <p>${document.getElementById('maturity').value} ${document.getElementById('maturity').value == 1 ? 'year' : 'years'}</p>
                </div>
                <div class="data-item">
                    <h4>Volatility</h4>
                    <p>${data.historical_volatility ? (data.historical_volatility * 100).toFixed(1) : 'N/A'}%</p>
                </div>
            `;
            
            // Add options explanation
            const optionsExplanation = document.createElement('div');
            optionsExplanation.className = 'options-explanation';
            
            let explanationHTML = `
                <h3>Options Analysis</h3>
                <p>This analysis shows the probabilities for ${data.symbol} options with a strike price of $${data.strike_price.toFixed(2)} 
                expiring in ${document.getElementById('maturity').value} ${document.getElementById('maturity').value == 1 ? 'year' : 'years'}.</p>
                
                <ul>
                    <li><strong>Call Option Probability:</strong> ${callProbability}% chance that ${data.symbol} will be above $${data.strike_price.toFixed(2)} at expiration.</li>
                    <li><strong>Put Option Probability:</strong> ${putProbability}% chance that ${data.symbol} will be below $${data.strike_price.toFixed(2)} at expiration.</li>
                </ul>
                
                <p>The expected future price is calculated based on the current price, volatility, and time to maturity.</p>
            `;
            
            // Add warning for unreasonable strike prices
            if (!isReasonableStrike) {
                explanationHTML += `
                    <div class="warning-note">
                        <p><strong>Note:</strong> The strike price you've selected ($${data.strike_price.toFixed(2)}) is 
                        ${strikePriceRatio < 0.5 ? 'significantly below' : 'significantly above'} the current price ($${data.current_price.toFixed(2)}).
                        Probability calculations become less reliable for strike prices that are very far from the current price.</p>
                    </div>
                `;
            }
            
            optionsExplanation.innerHTML = explanationHTML;
            
            // Append explanation after the data grid
            pricingDataGrid.parentNode.insertBefore(optionsExplanation, pricingDataGrid.nextSibling);
            
            // Hide valuation summary if it exists
            document.getElementById('valuation-summary').style.display = 'none';
            
        } else {
            // Calculate if stock is overvalued or undervalued
            const currentPrice = data.current_price;
            const intrinsicValue = data.intrinsic_value_per_share;
            const valuationDiff = ((currentPrice - intrinsicValue) / intrinsicValue * 100).toFixed(1);
            const isOvervalued = currentPrice > intrinsicValue;
            
            pricingDataGrid.innerHTML = `
                <div class="data-item ${isOvervalued ? 'negative' : 'positive'}">
                    <h4>Intrinsic Value</h4>
                    <p>$${intrinsicValue.toFixed(2)}</p>
                </div>
                <div class="data-item">
                    <h4>Current Price</h4>
                    <p>$${currentPrice.toFixed(2)}</p>
                </div>
                <div class="data-item ${isOvervalued ? 'negative' : 'positive'}">
                    <h4>Valuation</h4>
                    <p>${isOvervalued ? 'Overvalued' : 'Undervalued'} by ${Math.abs(valuationDiff)}%</p>
                </div>
                <div class="data-item">
                    <h4>Expected Price (${document.getElementById('maturity').value}yr)</h4>
                    <p>$${data.expected_price.toFixed(2)}</p>
                </div>
                <div class="data-item">
                    <h4>Free Cash Flow</h4>
                    <p>$${data.fcf.toFixed(2)}B</p>
                </div>
                <div class="data-item">
                    <h4>Growth Rate</h4>
                    <p>${(data.growth_rate * 100).toFixed(1)}%</p>
                </div>
                <div class="data-item">
                    <h4>Discount Rate</h4>
                    <p>${(data.discount_rate * 100).toFixed(1)}%</p>
                </div>
                <div class="data-item">
                    <h4>P/E Ratio</h4>
                    <p>${data.pe_ratio.toFixed(2)}</p>
                </div>
                <div class="data-item">
                    <h4>Earnings Growth</h4>
                    <p>${(data.earnings_growth * 100).toFixed(1)}%</p>
                </div>
                <div class="data-item">
                    <h4>PEG Ratio</h4>
                    <p>${data.peg_ratio ? data.peg_ratio.toFixed(2) : 'N/A'}</p>
                </div>
            `;
            
            // Add valuation summary
            document.getElementById('valuation-summary').innerHTML = `
                <h3>Valuation Summary</h3>
                <p>Based on our analysis, ${data.symbol} is currently 
                <strong class="${isOvervalued ? 'negative' : 'positive'}">${isOvervalued ? 'overvalued' : 'undervalued'} by ${Math.abs(valuationDiff)}%</strong>. 
                The intrinsic value is estimated at <strong>$${intrinsicValue.toFixed(2)}</strong> compared to the current market price of 
                <strong>$${currentPrice.toFixed(2)}</strong>.</p>
                <p>This valuation is based on a DCF model with a growth rate of ${(data.growth_rate * 100).toFixed(1)}% 
                and a discount rate of ${(data.discount_rate * 100).toFixed(1)}%.</p>
            `;
            document.getElementById('valuation-summary').style.display = 'block';
        }
        
        // Add animation to highlight the new data
        const dataItems = pricingDataGrid.querySelectorAll('.data-item');
        dataItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('pulse');
                setTimeout(() => {
                    item.classList.remove('pulse');
                }, 500);
            }, index * 100);
        });
    }
    
    // Function to render valuation chart
    function renderValuationChart(data) {
        const chartContainer = document.getElementById('valuation-chart');
        chartContainer.style.display = 'block';
        
        // Show loading indicator
        chartContainer.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Loading historical data...</p>
        `;
        
        // Fetch historical data
        const symbol = data.symbol;
        const period = '1y'; // Default to 1 year
        
        fetch(`/historical-data?symbol=${symbol}&period=${period}`)
            .then(response => response.json())
            .then(histData => {
                if (histData.error) {
                    chartContainer.innerHTML = `<p class="error-message">${histData.error}</p>`;
                    return;
                }
                
                // Clear loading indicator
                chartContainer.innerHTML = '<canvas id="chart"></canvas>';
                
                // If Chart.js is loaded, create a chart
                if (typeof Chart !== 'undefined') {
                    const ctx = document.getElementById('chart').getContext('2d');
                    
                    // Create a line chart with historical data
                    window.valuationChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: histData.dates,
                            datasets: [
                                {
                                    label: 'Current Price',
                                    data: histData.prices,
                                    borderColor: histData.valuation_diff_percent > 0 ? 'rgba(231, 76, 60, 1)' : 'rgba(52, 152, 219, 1)',
                                    backgroundColor: 'rgba(0, 0, 0, 0)',
                                    borderWidth: 2,
                                    pointRadius: 0,
                                    pointHoverRadius: 5,
                                    tension: 0.1
                                },
                                {
                                    label: 'Intrinsic Value',
                                    data: histData.intrinsic_values,
                                    borderColor: 'rgba(46, 204, 113, 1)',
                                    backgroundColor: 'rgba(0, 0, 0, 0)',
                                    borderWidth: 2,
                                    pointRadius: 0,
                                    pointHoverRadius: 5,
                                    tension: 0.1
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            const value = context.raw;
                                            return `${context.dataset.label}: $${value.toFixed(2)}`;
                                        }
                                    }
                                },
                                legend: {
                                    display: true,
                                    position: 'top',
                                    labels: {
                                        font: {
                                            size: 14
                                        }
                                    }
                                }
                            },
                            layout: {
                                padding: {
                                    bottom: 30 // Add more padding at the bottom
                                }
                            },
                            scales: {
                                y: {
                                    ticks: {
                                        display: false, // Hide y-axis labels by default
                                        callback: function(value) {
                                            return '$' + value.toFixed(2);
                                        },
                                        font: {
                                            size: 12
                                        }
                                    },
                                    grid: {
                                        color: 'rgba(0, 0, 0, 0.05)' // Lighter grid lines
                                    },
                                    title: {
                                        display: false // Hide y-axis title
                                    }
                                },
                                x: {
                                    ticks: {
                                        display: false, // Hide x-axis labels by default
                                        maxRotation: 45,
                                        minRotation: 45
                                    },
                                    grid: {
                                        display: false // Hide x-axis grid lines
                                    }
                                }
                            },
                            hover: {
                                mode: 'index',
                                intersect: false,
                                onHover: function(event, elements) {
                                    // Show ticks when hovering
                                    if (elements && elements.length) {
                                        window.valuationChart.config.options.scales.y.ticks.display = true;
                                        window.valuationChart.config.options.scales.x.ticks.display = true;
                                    } else {
                                        window.valuationChart.config.options.scales.y.ticks.display = false;
                                        window.valuationChart.config.options.scales.x.ticks.display = false;
                                    }
                                    window.valuationChart.update();
                                }
                            }
                        }
                    });
                    
                    // Add a title above the chart
                    const chartTitle = document.createElement('h3');
                    chartTitle.textContent = `${symbol} Valuation Comparison`;
                    chartTitle.style.textAlign = 'center';
                    chartTitle.style.marginBottom = '1rem';
                    
                    // Insert title before the canvas
                    const canvas = chartContainer.querySelector('canvas');
                    chartContainer.insertBefore(chartTitle, canvas);
                    
                    // Add period selector
                    const periodSelector = document.createElement('div');
                    periodSelector.className = 'period-selector';
                    periodSelector.innerHTML = `
                        <button class="btn btn-small ${period === '1mo' ? 'active' : ''}" data-period="1mo">1M</button>
                        <button class="btn btn-small ${period === '3mo' ? 'active' : ''}" data-period="3mo">3M</button>
                        <button class="btn btn-small ${period === '6mo' ? 'active' : ''}" data-period="6mo">6M</button>
                        <button class="btn btn-small ${period === '1y' ? 'active' : ''}" data-period="1y">1Y</button>
                        <button class="btn btn-small ${period === '2y' ? 'active' : ''}" data-period="2y">2Y</button>
                        <button class="btn btn-small ${period === '5y' ? 'active' : ''}" data-period="5y">5Y</button>
                    `;
                    
                    // Add event listeners to period buttons
                    periodSelector.querySelectorAll('button').forEach(btn => {
                        btn.addEventListener('click', () => {
                            const newPeriod = btn.getAttribute('data-period');
                            updateChartPeriod(symbol, newPeriod);
                            
                            // Update active button
                            periodSelector.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                            btn.classList.add('active');
                        });
                    });
                    
                    // Append period selector
                    chartContainer.appendChild(periodSelector);
                }
            })
            .catch(error => {
                console.error('Error fetching historical data:', error);
                chartContainer.innerHTML = `<p class="error-message">Failed to load historical data. Please try again.</p>`;
            });
    }
    
    // Function to update chart period
    function updateChartPeriod(symbol, period) {
        const chartContainer = document.getElementById('valuation-chart');
        
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-overlay';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Loading data...</p>
        `;
        chartContainer.appendChild(loadingIndicator);
        
        // Fetch historical data for new period
        fetch(`/historical-data?symbol=${symbol}&period=${period}`)
            .then(response => response.json())
            .then(histData => {
                // Remove loading indicator
                chartContainer.querySelector('.loading-overlay').remove();
                
                if (histData.error) {
                    console.error('Error fetching historical data:', histData.error);
                    return;
                }
                
                // Update chart with new data
                if (window.valuationChart) {
                    window.valuationChart.data.labels = histData.dates;
                    window.valuationChart.data.datasets[0].data = histData.prices;
                    window.valuationChart.data.datasets[1].data = histData.intrinsic_values;
                    
                    // Preserve the current display settings for ticks
                    const yTicksDisplay = window.valuationChart.config.options.scales.y.ticks.display;
                    const xTicksDisplay = window.valuationChart.config.options.scales.x.ticks.display;
                    
                    window.valuationChart.update();
                    
                    // Restore the display settings after update
                    window.valuationChart.config.options.scales.y.ticks.display = yTicksDisplay;
                    window.valuationChart.config.options.scales.x.ticks.display = xTicksDisplay;
                    window.valuationChart.update();
                }
            })
            .catch(error => {
                console.error('Error updating chart period:', error);
                chartContainer.querySelector('.loading-overlay').remove();
            });
    }
    
    // Helper functions
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
    
    function hideError() {
        errorMessage.style.display = 'none';
    }
    
    function showLoading(show) {
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
    
    // Add tooltips for financial terms
    const tooltips = {
        'intrinsic-value': 'The calculated true value of a stock based on future cash flows.',
        'fcf': 'Free Cash Flow - The cash a company generates after accounting for cash outflows to support operations.',
        'growth-rate': 'The expected annual growth rate of the company\'s cash flows.',
        'discount-rate': 'The rate used to discount future cash flows to present value, reflecting risk and opportunity cost.',
        'pe-ratio': 'Price-to-Earnings Ratio - A valuation ratio of a company\'s current share price compared to its earnings per share.',
        'peg-ratio': 'Price/Earnings to Growth Ratio - A stock\'s P/E ratio divided by its growth rate, used to determine value while considering growth.',
        'volatility': 'A statistical measure of the dispersion of returns for a given security or market index.',
        'call-option': 'A financial contract that gives the buyer the right to purchase a stock at a specified price within a specific time period.',
        'put-option': 'A financial contract that gives the buyer the right to sell a stock at a specified price within a specific time period.'
    };
    
    // Add tooltip functionality
    document.querySelectorAll('.tooltip').forEach(tooltip => {
        const term = tooltip.getAttribute('data-term');
        if (tooltips[term]) {
            const tooltipText = document.createElement('span');
            tooltipText.className = 'tooltip-text';
            tooltipText.textContent = tooltips[term];
            tooltip.appendChild(tooltipText);
        }
    });
}); 