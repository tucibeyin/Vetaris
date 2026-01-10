
document.addEventListener('DOMContentLoaded', () => {
    fetchProducts();
});

async function fetchProducts() {
    const productsGrid = document.getElementById('products-grid');
    
    try {
        const response = await fetch('/api/products');
        if (!response.ok) {
            throw new Error('Veri çekilemedi');
        }
        
        const products = await response.json();
        
        // Clear loading state
        productsGrid.innerHTML = '';
        
        products.forEach(product => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });
        
    } catch (error) {
        console.error('Hata:', error);
        productsGrid.innerHTML = '<p class="error">Ürünler yüklenirken bir sorun oluştu.</p>';
    }
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    card.innerHTML = `
        <img src="${product.image}" alt="${product.name}" class="product-image" loading="lazy">
        <div class="product-info">
            <span class="product-category">${product.category}</span>
            <h3 class="product-title">${product.name}</h3>
            <p class="product-desc">${product.description}</p>
            <div class="product-footer">
                <span class="product-price">${product.price.toFixed(2)} ₺</span>
                <button class="btn-add" onclick="addToCart(${product.id})">Sepete Ekle</button>
            </div>
        </div>
    `;
    
    return card;
}

function addToCart(productId) {
    // Simple interactions for now
    alert('Ürün sepete eklendi! (Demo)');
    console.log(`Ürün ${productId} sepete eklendi`);
}
