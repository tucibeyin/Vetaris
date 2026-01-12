
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    // Only fetch products if we are on the home page (grid exists)
    if (document.getElementById('products-grid')) {
        fetchProducts();
    }

    // Auth Form Listeners
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

// Global variable for products
let allProducts = [];

async function fetchProducts() {
    const productsGrid = document.getElementById('products-grid');

    try {
        const response = await fetch('/api/products');
        if (!response.ok) {
            throw new Error('Veri çekilemedi');
        }

        allProducts = await response.json(); // Store locally

        // Clear loading state
        productsGrid.innerHTML = '';

        allProducts.forEach(product => {
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
    // Make card clickable for modal (except buttons)
    card.style.cursor = 'pointer';
    card.onclick = (e) => {
        // Sepete ekle butonuna basıldıysa modal açma
        if (!e.target.classList.contains('btn-add')) {
            openModal(product);
        }
    };

    card.innerHTML = `
        <img src="${product.image}" alt="${product.name}" class="product-image" loading="lazy">
        <div class="product-info">
            <span class="product-category">${product.category}</span>
            <h3 class="product-title">${product.name}</h3>
            <p class="product-desc">${product.description.substring(0, 60)}...</p>
            <div class="product-footer">
                <span class="product-price">${product.price.toFixed(2)} ₺</span>
                <button class="btn-add" onclick="addToCart(${product.id})">Sepete Ekle</button>
            </div>
        </div>
    `;

    return card;
}

function addToCart(productId) {
    // Stop propagation handled in onclick above by checking target, but button onclick needs to function.
    // Actually the onclick attribute usually fires first.
    // Let's rely on event bubbling check in card.onclick
    alert('Ürün sepete eklendi! (Demo)');
    console.log(`Ürün ${productId} sepete eklendi`);
}

// Modal Logic
const modal = document.getElementById('product-modal');
const closeModalBtn = document.querySelector('.close-modal');

if (closeModalBtn) {
    closeModalBtn.onclick = () => {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300); // Wait for transition
    };
}

window.onclick = (event) => {
    if (event.target == modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
};

function openModal(product) {
    document.getElementById('modal-image').src = product.image;
    document.getElementById('modal-title').innerText = product.name;
    document.getElementById('modal-category').innerText = product.category;
    document.getElementById('modal-desc').innerText = product.description;
    document.getElementById('modal-price').innerText = product.price.toFixed(2) + ' ₺';

    // Setup modal button
    const modalBtn = document.getElementById('modal-add-btn');
    modalBtn.onclick = () => addToCart(product.id);

    modal.style.display = 'flex';
    // Trigger reflow
    void modal.offsetWidth;
    modal.classList.add('active');
}

// Auth Logic
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();

        updateNavAuth(data.authenticated, data.email);
    } catch (error) {
        console.error('Auth Check Error:', error);
    }
}

function updateNavAuth(isAuthenticated, email) {
    const navLinks = document.querySelector('.nav-links');
    // We assume the last link is "Giriş Yap" or "Hesabım"
    // Let's find or create the auth link item
    let authItem = document.getElementById('nav-auth-item');

    if (!authItem) {
        // Find existing list to append or modify
        if (!navLinks) return; // e.g. on clean pages if any
        authItem = document.createElement('li');
        authItem.id = 'nav-auth-item';
        navLinks.appendChild(authItem);
    }

    if (isAuthenticated) {
        authItem.innerHTML = `<a href="#" onclick="handleLogout(event)">Çıkış Yap (${email})</a>`;
    } else {
        authItem.innerHTML = `<a href="login.html">Giriş Yap</a>`;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = 'index.html';
        } else {
            alert('Giriş başarısız: ' + data.error);
        }
    } catch (error) {
        console.error('Login Error:', error);
        alert('Bir hata oluştu.');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        alert('Şifreler eşleşmiyor!');
        return;
    }

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Kayıt başarılı! Giriş yapabilirsiniz.');
            window.location.href = 'login.html';
        } else {
            alert('Kayıt başarısız: ' + data.error);
        }
    } catch (error) {
        console.error('Register Error:', error);
        alert('Bir hata oluştu.');
    }
}

async function handleLogout(e) {
    e.preventDefault();
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        window.location.href = 'login.html'; // or refresh index
    } catch (error) {
        console.error('Logout Error:', error);
    }
}

// Mobile Menu Logic
const hamburger = document.querySelector('.hamburger-menu');
const navLinks = document.querySelector('.nav-links');

if (hamburger) {
    hamburger.onclick = () => {
        navLinks.classList.toggle('active');
    };
}
