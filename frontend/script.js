const API = "http://127.0.0.1:8000/api/v1";
let chart;
let priceCharts = {}; // Store charts for each symbol

async function refresh() {
    try {
        const [insts, ports, trades, stats] = await Promise.all([
            fetch(`${API}/instruments`).then(r => {
                if (!r.ok) throw new Error(`Instruments API error: ${r.status}`);
                return r.json();
            }),
            fetch(`${API}/portfolio`).then(r => {
                if (!r.ok) throw new Error(`Portfolio API error: ${r.status}`);
                return r.json();
            }),
            fetch(`${API}/trades`).then(r => {
                if (!r.ok) throw new Error(`Trades API error: ${r.status}`);
                return r.json();
            }),
            fetch(`${API}/stats`).then(r => {
                if (!r.ok) throw new Error(`Stats API error: ${r.status}`);
                return r.json();
            })
        ]);

    // Update chart with all instruments
    updateChart(insts);
    
    // Render Watchlist
    document.getElementById('watchlist').innerHTML = insts.map(s => {
        const price = s.lastTradedPrice || s.price || 0;
        const change = s.change || 0;
        const changePercent = s.changePercent || 0;
        const changeColor = change >= 0 ? '#10b981' : '#f43f5e';
        const changeIcon = change >= 0 ? '▲' : '▼';
        
        return `
        <div class="row">
            <div class="stock-info">
                <div class="stock-header">
                    <span><strong>${s.symbol}</strong></span>
                    <span class="stock-volume">Vol: ${(s.volume || 0).toLocaleString()}</span>
                </div>
                <div class="stock-price-row">
                    <span class="stock-price">$${price.toFixed(2)}</span>
                    <span class="stock-change" style="color: ${changeColor}">
                        ${changeIcon} ${Math.abs(change).toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)
                    </span>
                </div>
                <div class="stock-range">
                    <span>H: $${(s.high || price || 0).toFixed(2)}</span>
                    <span>L: $${(s.low || price || 0).toFixed(2)}</span>
                </div>
            </div>
            <div class="order-controls">
                <input type="number" id="qty-${s.symbol}" value="1" min="1" class="qty-input" />
                <button class="buy-btn" onclick="order('${s.symbol}', 'BUY')" type="button">BUY</button>
            </div>
        </div>`;
    }).join('');

    // Render Portfolio
    document.getElementById('portfolio-body').innerHTML = ports.length > 0 ? ports.map(p => {
        const avgPrice = p.averagePrice || p.avgPrice || 0;
        const currentPrice = p.currentPrice || avgPrice;
        const unrealizedPnl = p.unrealizedPnl || 0;
        const change = p.change || 0;
        const changePercent = p.changePercent || 0;
        const pnlColor = unrealizedPnl >= 0 ? '#10b981' : '#f43f5e';
        const changeColor = change >= 0 ? '#10b981' : '#f43f5e';
        const changeIcon = change >= 0 ? '▲' : '▼';
        return `
        <tr>
            <td><strong>${p.symbol}</strong></td>
            <td>${p.quantity}</td>
            <td>$${avgPrice.toFixed(2)}</td>
            <td>
                <div>$${currentPrice.toFixed(2)}</div>
                <div style="color: ${changeColor}; font-size: 11px;">
                    ${changeIcon} ${Math.abs(change).toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%)
                </div>
            </td>
            <td style="color: ${pnlColor}">$${unrealizedPnl >= 0 ? '+' : ''}${unrealizedPnl.toFixed(2)}</td>
            <td>
                <div class="order-controls">
                    <input type="number" id="sell-qty-${p.symbol}" value="1" min="1" max="${p.quantity}" class="qty-input" />
                    <button class="sell-btn" onclick="order('${p.symbol}', 'SELL')" type="button">SELL</button>
                </div>
            </td>
        </tr>`;
    }).join('') : '<tr><td colspan="6" style="text-align: center; color: #64748b;">No holdings</td></tr>';

    // Render History
    document.getElementById('history-list').innerHTML = trades.map(t => `
        <div class="history-item ${t.side.toLowerCase()}">
            <span>${t.side} ${t.qty} ${t.symbol} @ $${t.price}</span>
            <span style="color:${t.pnl >= 0 ? '#10b981' : '#f43f5e'}">${t.pnl !== 0 ? '$' + t.pnl : ''}</span>
        </div>`).join('');

    // Update P&L
    const pnlEl = document.getElementById('pnl-display');
    if (pnlEl) {
        pnlEl.innerText = `Profit/Loss: $${stats.total_pnl.toFixed(2)}`;
        pnlEl.style.color = stats.total_pnl >= 0 ? '#10b981' : '#f43f5e';
    }
    } catch (error) {
        console.error('Refresh error:', error);
        // Don't alert on every refresh error, just log it
    }
}

async function order(symbol, side) {
    try {
        // Get quantity from input field
        const qtyInputId = side === 'BUY' ? `qty-${symbol}` : `sell-qty-${symbol}`;
        const qtyInput = document.getElementById(qtyInputId);
        const quantity = qtyInput ? parseInt(qtyInput.value) || 1 : 1;
        
        if (quantity < 1) {
            alert('Quantity must be at least 1');
            return;
        }
        
        const response = await fetch(`${API}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity, side, style: "MARKET" })
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(`Error: ${error.detail || 'Failed to place order'}`);
            return;
        }
        
        const result = await response.json();
        console.log(`Order placed: ${side} ${quantity} ${symbol}`, result);
        
        // Show success message in console
        console.log(`✓ Order ${result.status}: ${side} ${quantity} ${symbol} - Refreshing UI...`);
        
        // Wait a moment for order to process, then refresh multiple times to ensure update
        setTimeout(() => {
            refresh();
        }, 300);
        
        // Refresh again after a short delay to catch any async updates
        setTimeout(() => {
            refresh();
        }, 1000);
    } catch (error) {
        console.error('Order error:', error);
        alert('Failed to connect to server. Make sure the backend is running.');
    }
}

function initChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ 
                label: 'Market Index', 
                data: [], 
                borderColor: '#3b82f6', 
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        },
        options: { 
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: { 
                y: { 
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            size: 10
                        }
                    }
                }, 
                x: { 
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            size: 10
                        }
                    }
                } 
            }, 
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(21, 28, 44, 0.95)',
                    titleColor: '#e2e8f0',
                    bodyColor: '#e2e8f0',
                    borderColor: '#232d42',
                    borderWidth: 1,
                    displayColors: false
                }
            },
            animation: { 
                duration: 500 
            }
        }
    });
}

function updateChart(instruments) {
    if (!chart || !instruments || instruments.length === 0) return;
    
    // Calculate market index (average of current prices from all stocks)
    const currentPrices = instruments
        .map(inst => inst.lastTradedPrice || inst.price || 0)
        .filter(price => price && price > 0);
    
    if (currentPrices.length === 0) return;
    
    const avgPrice = currentPrices.reduce((a, b) => a + b, 0) / currentPrices.length;
    
    // Update chart data
    if (chart.data.datasets[0].data.length === 0) {
        // Initialize with current average
        chart.data.datasets[0].data = Array(20).fill(avgPrice);
        chart.data.labels = Array(20).fill('').map((_, i) => i);
    } else {
        // Add new data point
        chart.data.datasets[0].data.push(avgPrice);
        const nextLabel = chart.data.labels.length > 0 
            ? Math.max(...chart.data.labels) + 1 
            : chart.data.labels.length;
        chart.data.labels.push(nextLabel);
        
        // Keep only last 50 points for performance
        if (chart.data.datasets[0].data.length > 50) {
            chart.data.datasets[0].data.shift();
            chart.data.labels.shift();
        }
    }
    
    // Update chart smoothly without animation on every update
    chart.update('none');
}

// Initialize chart when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initChart();
        refresh();
    });
} else {
    initChart();
    refresh();
}

// Update every 2-3 seconds for realistic simulation
setInterval(refresh, 2500);