
// Cart State
let cart = JSON.parse(localStorage.getItem('cart')) || [];
let currentHeroIndex = 0;
let heroProducts = [];

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    updateCartIcon();

    // Only fetch products if we are on the home page
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

    // Render Cart Modal Items
    renderCartItems();
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

        allProducts = await response.json();

        productsGrid.innerHTML = '';

        allProducts.forEach(product => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });

        // Initialize Hero Carousel if we are on the homepage
        if (document.getElementById('hero-carousel-track')) {
            initHeroCarousel(allProducts);
        }

    } catch (error) {
        console.error('Hata:', error);
        productsGrid.innerHTML = '<p class="error">Ürünler yüklenirken bir sorun oluştu.</p>';
    }
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.style.cursor = 'pointer';
    card.onclick = (e) => {
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
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;

    const existingItem = cart.find(item => item.id === productId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ ...product, quantity: 1 });
    }

    saveCart();
    updateCartIcon();
    renderCartItems();

    // Visual feedback
    alert(`${product.name} sepete eklendi!`);
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function updateCartIcon() {
    const count = cart.reduce((acc, item) => acc + item.quantity, 0);
    const cartCountEl = document.querySelector('.cart-count');
    if (cartCountEl) {
        cartCountEl.innerText = count;
    }
}

function renderCartItems() {
    const container = document.querySelector('.cart-items');
    const totalEl = document.querySelector('.total-price');
    if (!container) return;

    if (cart.length === 0) {
        container.innerHTML = '<p class="empty-cart-msg">Sepetiniz boş.</p>';
        if (totalEl) totalEl.innerText = 'Toplam: 0.00 ₺';
        return;
    }

    let total = 0;
    container.innerHTML = cart.map(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        return `
            <div class="cart-item" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                <div style="flex-grow: 1;">
                    <div><strong>${item.name}</strong></div>
                    <div style="font-size: 0.9em; color: #666;">${item.quantity} x ${item.price.toFixed(2)} ₺</div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span>${itemTotal.toFixed(2)} ₺</span>
                    <span onclick="removeFromCart(${item.id})" style="cursor: pointer; color: #dc3545; font-size: 1.2rem;" title="Sil">&times;</span>
                </div>
            </div>
        `;
    }).join('');

    if (totalEl) totalEl.innerText = `Toplam: ${total.toFixed(2)} ₺`;
}

function removeFromCart(productId) {
    const itemIndex = cart.findIndex(item => item.id === productId);
    if (itemIndex > -1) {
        if (cart[itemIndex].quantity > 1) {
            cart[itemIndex].quantity -= 1;
        } else {
            cart.splice(itemIndex, 1);
        }
        saveCart();
        updateCartIcon();
        renderCartItems();
    }
}

function toggleCart() {
    const modal = document.getElementById('cart-modal');
    if (modal) {
        modal.classList.toggle('active');
        // Render when opening just in case
        renderCartItems();
    }
}

// Checkout
async function checkout() {
    // Check if cart is empty
    if (cart.length === 0) {
        alert('Sepetiniz boş.');
        return;
    }

    // Check Auth first
    try {
        const res = await fetch('/api/auth/me');
        if (!res.ok) {
            alert('Lütfen önce giriş yapın.');
            window.location.href = 'login.html';
            return;
        }
        const data = await res.json();
        if (!data.authenticated) {
            alert('Lütfen önce giriş yapın.');
            window.location.href = 'login.html';
            return;
        }

        // If authenticated, redirect to Checkout Page
        window.location.href = 'checkout.html';

    } catch (e) {
        window.location.href = 'login.html';
    }
}

// Modal Logic for Product Details
const modal = document.getElementById('product-modal');
const closeModalBtn = document.querySelector('.close-modal');

if (closeModalBtn) {
    closeModalBtn.onclick = () => {
        modal.classList.remove('active');
        setTimeout(() => { modal.style.display = 'none'; }, 300);
    };
}

if (modal) {
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('active');
            setTimeout(() => { modal.style.display = 'none'; }, 300);
        }
    };
}

function openModal(product) {
    document.getElementById('modal-image').src = product.image;
    document.getElementById('modal-title').innerText = product.name;
    document.getElementById('modal-category').innerText = product.category;
    document.getElementById('modal-desc').innerText = product.description;
    document.getElementById('modal-price').innerText = product.price.toFixed(2) + ' ₺';

    const modalBtn = document.getElementById('modal-add-btn');
    modalBtn.onclick = () => addToCart(product.id);

    modal.style.display = 'flex';
    void modal.offsetWidth;
    modal.classList.add('active');
}

// Auth Logic
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();

        if (response.ok && data.authenticated) {
            updateNavAuth(true, data.email, data.is_admin);
            return true; // Return status for promises
        } else {
            updateNavAuth(false);
            return false;
        }
    } catch (error) {
        console.error('Auth Check Error:', error);
        updateNavAuth(false);
        return false;
    }
}

function updateNavAuth(isAuthenticated, email, isAdmin) {
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;

    const existingAuthItems = navLinks.querySelectorAll('.auth-item-container, .auth-item');
    existingAuthItems.forEach(item => item.remove());

    const authContainer = document.createElement('div');
    authContainer.className = 'auth-item-container auth-btn-group-start';

    if (isAuthenticated) {
        // Admin Link
        if (isAdmin) {
            const adminLink = document.createElement('a');
            adminLink.href = 'admin.html';
            adminLink.className = 'btn-auth-login';
            adminLink.style.backgroundColor = '#d63031'; // Red distinct color
            adminLink.style.color = '#fff';
            adminLink.style.marginRight = '10px';
            adminLink.innerText = 'Admin Paneli';
            authContainer.appendChild(adminLink);
        }

        const accountLink = document.createElement('a');
        accountLink.href = 'account.html'; // Direct link to account page
        accountLink.className = 'btn-auth-login';
        accountLink.innerText = 'Hesabım';
        authContainer.appendChild(accountLink);

        const logoutLink = document.createElement('a');
        logoutLink.href = '#';
        logoutLink.className = 'btn-auth-logout';
        logoutLink.innerText = 'Çıkış Yap';
        logoutLink.onclick = handleLogout;
        authContainer.appendChild(logoutLink);
    } else {
        const loginLink = document.createElement('a');
        loginLink.href = 'login.html';
        loginLink.className = 'btn-auth-login';
        loginLink.innerText = 'Giriş Yap';
        authContainer.appendChild(loginLink);

        const registerLink = document.createElement('a');
        registerLink.href = 'register.html';
        registerLink.className = 'btn-auth-register';
        registerLink.innerText = 'Kayıt Ol';
        authContainer.appendChild(registerLink);
    }
    navLinks.appendChild(authContainer);
}

// Account Page Logic
async function loadAccountData() {
    const emailDisplay = document.getElementById('user-email-display');
    const initialDisplay = document.getElementById('user-initial');
    const ordersList = document.getElementById('orders-list');

    // 1. Get User Info
    try {
        const authResponse = await fetch('/api/auth/me');
        if (!authResponse.ok) {
            window.location.href = 'login.html';
            return;
        }
        const authData = await authResponse.json();

        if (emailDisplay) emailDisplay.innerText = authData.email;
        if (initialDisplay) initialDisplay.innerText = authData.email.charAt(0).toUpperCase();

        // 2. Get Orders
        const ordersResponse = await fetch('/api/orders');
        const orders = await ordersResponse.json();

        if (ordersList) {
            if (orders.length === 0) {
                ordersList.innerHTML = '<p>Henüz bir siparişiniz bulunmuyor.</p>';
            } else {
                ordersList.innerHTML = orders.map(order => {
                    const statusClass = order.status === 'Tamamlandı' ? 'status-tamamlandı' : 'status-hazırlanıyor';
                    const date = new Date(order.created_at).toLocaleDateString('tr-TR', {
                        year: 'numeric', month: 'long', day: 'numeric',
                        hour: '2-digit', minute: '2-digit'
                    });

                    const itemsHtml = order.items.map(item => `
                        <div class="order-item-row">
                            <span class="item-name">${item.product_name}</span>
                            <span>
                                <span class="item-qty">${item.quantity}x</span>
                                ${item.price_at_purchase.toFixed(2)} ₺
                            </span>
                        </div>
                    `).join('');

                    return `
                        <div class="order-card">
                            <div class="order-header">
                                <div>
                                    <div class="order-id">Sipariş #${order.id}</div>
                                    <div class="order-date">${date}</div>
                                </div>
                                <span class="order-status ${statusClass}">${order.status}</span>
                            </div>
                            <div class="order-items-list">
                                ${itemsHtml}
                            </div>
                            <div class="order-total">
                                Toplam: ${order.total_amount.toFixed(2)} ₺
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }

    } catch (error) {
        console.error('Account Data Error:', error);
        if (ordersList) ordersList.innerHTML = '<p class="text-danger">Bilgiler yüklenemedi.</p>';
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

const hamburger = document.querySelector('.hamburger-menu');
const navLinksEl = document.querySelector('.nav-links');
if (hamburger) {
    hamburger.onclick = () => {
        navLinksEl.classList.toggle('active');
    };
}

// --- Hero Carousel Logic ---
function initHeroCarousel(products) {
    heroProducts = products.filter(p => p.is_active); // Only show active
    if (heroProducts.length === 0) return;

    const track = document.getElementById('hero-carousel-track');
    track.innerHTML = '';

    heroProducts.forEach((p, index) => {
        const slide = document.createElement('div');
        slide.className = `hero-slide ${index === 0 ? 'active' : ''}`;
        if (index === heroProducts.length - 1) slide.className += ' prev-slide'; // Prepare for wrap around visually if needed, simpler logic used below

        // Reset classes for simple index logic
        slide.className = 'hero-slide';
        if (index === 0) slide.classList.add('active');

        slide.innerHTML = `
            <img src="${p.image}" alt="${p.name}">
            <h3>${p.name}</h3>
            <div class="price">${p.price} ₺</div>
        `;
        // Make slide clickable to go to details optionally
        slide.onclick = () => {
            // Redirect or open modal (using existing logic)
            openModal(p);
        };
        slide.style.cursor = 'pointer';

        track.appendChild(slide);
    });

    currentHeroIndex = 0;
}

function slideHero(direction) {
    if (heroProducts.length === 0) return;

    const slides = document.querySelectorAll('.hero-slide');

    // Hide current
    slides[currentHeroIndex].classList.remove('active');

    // Calculate next
    currentHeroIndex += direction;
    if (currentHeroIndex >= heroProducts.length) currentHeroIndex = 0;
    if (currentHeroIndex < 0) currentHeroIndex = heroProducts.length - 1;

    // Show next
    slides[currentHeroIndex].classList.add('active');
}

// Expose to window for onclick
window.slideHero = slideHero;
