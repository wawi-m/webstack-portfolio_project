// API endpoints
const API_BASE = '/api/v1';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const platformFilter = document.getElementById('platformFilter');
const productList = document.getElementById('productList');
const productModal = new bootstrap.Modal(document.getElementById('productModal'));

// Load products on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
});

// Search products
async function searchProducts() {
    const query = searchInput.value;
    const platform = platformFilter.value;
    showLoading();
    
    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (platform) params.append('platform', platform);
        
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
        const response = await fetch(`${API_BASE}/products`);
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
    showLoading();
    try {
        const [productResponse, visualizationResponse] = await Promise.all([
            fetch(`${API_BASE}/products/${productId}`),
            fetch(`${API_BASE}/products/${productId}/visualization/data`)
        ]);
        
        if (!productResponse.ok || !visualizationResponse.ok) {
            throw new Error('Failed to load product details');
        }
        
        const product = await productResponse.json();
        const visualizationData = await visualizationResponse.json();
        
        displayProductDetails(product);
        displayPriceChart(visualizationData);
        productModal.show();
    } catch (error) {
        showError('Error loading product details: ' + error.message);
    }
}

// Display product details in modal
function displayProductDetails(product) {
    const detailsContainer = document.getElementById('productDetails');
    detailsContainer.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <img src="${product.image_url || 'placeholder.jpg'}" class="img-fluid" 
                     alt="${product.name}" onerror="this.src='placeholder.jpg'">
            </div>
            <div class="col-md-8">
                <h4>${product.name}</h4>
                <p>Platform: ${product.platform}</p>
                <p>Current Price: $${formatPrice(product.current_price)}</p>
                <p>URL: <a href="${product.url}" target="_blank" rel="noopener noreferrer">
                    View on ${product.platform}</a></p>
            </div>
        </div>
    `;
}

// Display price history chart
function displayPriceChart(data) {
    const trace = {
        x: data.dates,
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

    const layout = {
        title: 'Price History',
        xaxis: { 
            title: 'Date',
            gridcolor: '#f5f5f5'
        },
        yaxis: { 
            title: 'Price ($)',
            gridcolor: '#f5f5f5'
        },
        paper_bgcolor: 'white',
        plot_bgcolor: 'white',
        margin: { t: 50, r: 20, l: 60, b: 50 }
    };

    const config = {
        responsive: true,
        displayModeBar: false
    };

    Plotly.newPlot('priceChart', [trace], layout, config);
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
