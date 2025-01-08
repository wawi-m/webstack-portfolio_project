// API endpoints
const API_BASE = '/api/v1';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const platformFilter = document.getElementById('platformFilter');
const categoryFilter = document.getElementById('categoryFilter');
const productList = document.getElementById('productList');
const productModal = new bootstrap.Modal(document.getElementById('productModal'));

// Load products on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    
    // Add event listeners for real-time filtering
    searchInput.addEventListener('input', debounce(searchProducts, 500));
    platformFilter.addEventListener('change', searchProducts);
    categoryFilter.addEventListener('change', searchProducts);
});

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search products
async function searchProducts() {
    const query = searchInput.value;
    const platform = platformFilter.value;
    const category = categoryFilter.value;
    showLoading();
    
    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (platform) params.append('platform', platform);
        if (category) params.append('category', category);
        
        const response = await fetch(`${API_BASE}/products/search?${params}`);
        if (!response.ok) throw new Error('Search failed');
        
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        showError('Error searching products: ' + error.message);
    }
}

// Load all products
async function loadProducts() {
    showLoading();
    try {
        const params = new URLSearchParams();
        const platform = platformFilter.value;
        const category = categoryFilter.value;
        
        if (platform) params.append('platform', platform);
        if (category) params.append('category', category);
        
        const response = await fetch(`${API_BASE}/products?${params}`);
        if (!response.ok) throw new Error('Failed to load products');
        
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        showError('Error loading products: ' + error.message);
    }
}

// Display products in grid
function displayProducts(products) {
    productList.innerHTML = '';
    
    if (products.length === 0) {
        productList.innerHTML = '<div class="col-12"><div class="alert alert-info">No products found</div></div>';
        return;
    }
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'col-md-4';
        card.innerHTML = `
            <div class="card product-card" onclick="showProductDetails(${product.id})">
                <img src="${product.image_url || 'placeholder.jpg'}" class="card-img-top product-image" 
                     alt="${product.name}" onerror="this.src='placeholder.jpg'">
                <div class="platform-badge">${product.platform}</div>
                <div class="category-badge">${product.category || 'Uncategorized'}</div>
                <div class="card-body">
                    <h5 class="card-title">${product.name}</h5>
                    <p class="card-text">Current Price: $${formatPrice(product.current_price)}</p>
                </div>
            </div>
        `;
        productList.appendChild(card);
    });
}

// Show product details and price history
async function showProductDetails(productId) {
    try {
        // Show loading state
        document.getElementById('productDetails').innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch all product data in parallel
        const [productResponse, priceHistoryResponse, visualizationResponse] = await Promise.all([
            fetch(`${API_BASE}/products/${productId}`),
            fetch(`${API_BASE}/products/${productId}/prices`),
            fetch(`${API_BASE}/products/${productId}/visualization/data`)
        ]);
        
        if (!productResponse.ok || !priceHistoryResponse.ok || !visualizationResponse.ok) {
            throw new Error('Failed to load product details');
        }
        
        const product = await productResponse.json();
        const priceHistory = await priceHistoryResponse.json();
        const visualizationData = await visualizationResponse.json();
        
        // Display product details
        document.getElementById('productDetails').innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <img src="${product.image_url || 'placeholder.jpg'}" class="img-fluid rounded" alt="${product.name}">
                </div>
                <div class="col-md-8">
                    <h4>${product.name}</h4>
                    <p class="text-muted">${product.platform}</p>
                    <p class="lead">KES ${formatPrice(product.current_price)}</p>
                    <p>${product.description || ''}</p>
                    <a href="${product.url}" target="_blank" class="btn btn-primary">View on ${product.platform}</a>
                </div>
            </div>
        `;
        
        // Display price statistics and chart
        displayPriceStats(priceHistory);
        displayPriceChart(visualizationData);
        
        // Store current product ID for updates
        currentProductId = productId;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('productDetails').innerHTML = `
            <div class="alert alert-danger">
                Error loading product details: ${error.message}
            </div>
        `;
    }
}

// Update price history for different time periods
async function updatePriceHistory(days) {
    if (!currentProductId) return;
    
    try {
        // Show loading state
        document.getElementById('priceChart').innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        // Fetch updated data
        const [historyResponse, visualizationResponse] = await Promise.all([
            fetch(`${API_BASE}/products/${currentProductId}/prices?days=${days}`),
            fetch(`${API_BASE}/products/${currentProductId}/visualization/data?days=${days}`)
        ]);
        
        if (!historyResponse.ok || !visualizationResponse.ok) {
            throw new Error('Failed to update price history');
        }
        
        const priceHistory = await historyResponse.json();
        const visualizationData = await visualizationResponse.json();
        
        // Update the display
        displayPriceStats(priceHistory);
        displayPriceChart(visualizationData);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('priceChart').innerHTML = `
            <div class="alert alert-danger">
                Error updating price history: ${error.message}
            </div>
        `;
    }
}

// Display price statistics
function displayPriceStats(priceHistory) {
    if (!priceHistory || priceHistory.length === 0) {
        document.getElementById('priceStats').innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">No price history available</div>
            </div>
        `;
        return;
    }
    
    const stats = calculatePriceStats(priceHistory);
    document.getElementById('priceStats').innerHTML = `
        <div class="col-md-3 col-6">
            <div class="stat-card">
                <div class="stat-title">Current Price</div>
                <div class="stat-value">KES ${formatPrice(stats.currentPrice)}</div>
                <div class="stat-change ${stats.priceChange >= 0 ? 'positive' : 'negative'}">
                    ${stats.priceChange >= 0 ? '▲' : '▼'} ${Math.abs(stats.priceChange)}%
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6">
            <div class="stat-card">
                <div class="stat-title">Lowest Price</div>
                <div class="stat-value">KES ${formatPrice(stats.lowestPrice)}</div>
            </div>
        </div>
        <div class="col-md-3 col-6">
            <div class="stat-card">
                <div class="stat-title">Highest Price</div>
                <div class="stat-value">KES ${formatPrice(stats.highestPrice)}</div>
            </div>
        </div>
        <div class="col-md-3 col-6">
            <div class="stat-card">
                <div class="stat-title">Average Price</div>
                <div class="stat-value">KES ${formatPrice(stats.averagePrice)}</div>
            </div>
        </div>
    `;
}

// Display price chart
function displayPriceChart(data) {
    if (!data || !data.prices || data.prices.length === 0) {
        document.getElementById('priceChart').innerHTML = `
            <div class="alert alert-info">No price history available for visualization</div>
        `;
        return;
    }

    const trace = {
        x: data.dates.map(date => new Date(date)),
        y: data.prices,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Price History',
        line: {
            color: '#007bff',
            width: 2
        },
        marker: {
            size: 6
        }
    };

    // Calculate 7-day moving average
    const ma7 = calculateMovingAverage(data.prices, 7);
    const maTrace = {
        x: data.dates.map(date => new Date(date)),
        y: ma7,
        type: 'scatter',
        mode: 'lines',
        name: '7-day Moving Average',
        line: {
            color: '#28a745',
            width: 2,
            dash: 'dash'
        }
    };

    const layout = {
        title: {
            text: 'Price History Trend',
            font: {
                size: 18
            }
        },
        xaxis: { 
            title: 'Date',
            gridcolor: '#f5f5f5',
            tickformat: '%Y-%m-%d'
        },
        yaxis: { 
            title: 'Price (KES)',
            gridcolor: '#f5f5f5'
        },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        margin: { t: 50, r: 20, l: 60, b: 50 },
        showlegend: true,
        legend: {
            x: 0,
            y: 1.1,
            orientation: 'h'
        },
        hovermode: 'x unified'
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    Plotly.newPlot('priceChart', [trace, maTrace], layout, config);
}

// Calculate moving average
function calculateMovingAverage(prices, window) {
    const result = [];
    for (let i = 0; i < prices.length; i++) {
        if (i < window - 1) {
            result.push(null);
            continue;
        }
        let sum = 0;
        for (let j = 0; j < window; j++) {
            sum += prices[i - j];
        }
        result.push(sum / window);
    }
    return result;
}

// Calculate price statistics
function calculatePriceStats(priceHistory) {
    const prices = priceHistory.map(item => item.price);
    const currentPrice = prices[0] || 0;
    const oldestPrice = prices[prices.length - 1] || currentPrice;
    
    return {
        currentPrice: currentPrice,
        lowestPrice: Math.min(...prices),
        highestPrice: Math.max(...prices),
        averagePrice: prices.reduce((a, b) => a + b, 0) / prices.length,
        priceChange: oldestPrice ? ((currentPrice - oldestPrice) / oldestPrice * 100).toFixed(1) : 0
    };
}

// Helper functions
function showLoading() {
    productList.innerHTML = '<div class="col-12"><div class="loading">Loading...</div></div>';
}

function showError(message) {
    productList.innerHTML = `
        <div class="col-12">
            <div class="error-message">${message}</div>
        </div>
    `;
}

function formatPrice(price) {
    return typeof price === 'number' ? price.toFixed(2) : '0.00';
}

// Store the current product ID for price history updates
let currentProductId;
