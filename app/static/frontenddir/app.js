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
    
    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (platform) params.append('platform', platform);
        
        const response = await fetch(`${API_BASE}/products/search?${params}`);
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        showError('Error searching products');
    }
}

// Load all products
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE}/products`);
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        showError('Error loading products');
    }
}

// Display products in grid
function displayProducts(products) {
    productList.innerHTML = '';
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'col-md-4';
        card.innerHTML = `
            <div class="card product-card" onclick="showProductDetails(${product.id})">
                <img src="${product.image_url}" class="card-img-top product-image" alt="${product.name}">
                <div class="platform-badge">${product.platform}</div>
                <div class="card-body">
                    <h5 class="card-title">${product.name}</h5>
                    <p class="card-text">Current Price: $${product.current_price}</p>
                </div>
            </div>
        `;
        productList.appendChild(card);
    });
}

// Show product details and price history
async function showProductDetails(productId) {
    try {
        const [productResponse, visualizationResponse] = await Promise.all([
            fetch(`${API_BASE}/products/${productId}`),
            fetch(`${API_BASE}/products/${productId}/visualization/data`)
        ]);
        
        const product = await productResponse.json();
        const visualizationData = await visualizationResponse.json();
        
        displayProductDetails(product);
        displayPriceChart(visualizationData);
        productModal.show();
    } catch (error) {
        showError('Error loading product details');
    }
}

// Display product details in modal
function displayProductDetails(product) {
    const detailsContainer = document.getElementById('productDetails');
    detailsContainer.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <img src="${product.image_url}" class="img-fluid" alt="${product.name}">
            </div>
            <div class="col-md-8">
                <h4>${product.name}</h4>
                <p>Platform: ${product.platform}</p>
                <p>Current Price: $${product.current_price}</p>
                <p>URL: <a href="${product.url}" target="_blank">View on ${product.platform}</a></p>
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
        name: 'Price History'
    };

    const layout = {
        title: 'Price History',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Price ($)' }
    };

    Plotly.newPlot('priceChart', [trace], layout);
}

// Show error message
function showError(message) {
    productList.innerHTML = `
        <div class="col-12">
            <div class="error-message">${message}</div>
        </div>
    `;
}
