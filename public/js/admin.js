document.addEventListener('DOMContentLoaded', () => {
    checkAdminAuth();
    setupNavigation();
    setupModals();
});

let PRODUCTS = [];
let ORDERS = [];

// --- Auth ---
async function checkAdminAuth() {
    try {
        const res = await fetch('/api/auth/me');
        if (!res.ok) throw new Error('Auth fetch failed');
        const data = await res.json();

        if (!data.authenticated || !data.is_admin) {
            window.location.href = '/account.html';
        } else {
            // Initial Load
            loadDashboard();
        }
    } catch (e) {
        window.location.href = '/account.html';
    }
}

document.getElementById('logoutBtn').addEventListener('click', async (e) => {
    e.preventDefault();
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/index.html';
});

// --- Navigation ---
function setupNavigation() {
    const links = document.querySelectorAll('.nav-link[data-page]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            // Active State
            links.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // View Switching
            const page = link.dataset.page;
            document.querySelectorAll('.admin-view').forEach(view => view.classList.add('hidden'));
            document.getElementById(`view-${page}`).classList.remove('hidden');

            // Load Data
            if (page === 'dashboard') loadDashboard();
            if (page === 'products') loadProducts();
            if (page === 'orders') loadOrders();
        });
    });
}

// --- Dashboard ---
async function loadDashboard() {
    await Promise.all([fetchProducts(), fetchOrders()]);

    document.getElementById('total-orders-count').innerText = ORDERS.length;
    document.getElementById('total-products-count').innerText = PRODUCTS.length;

    const pending = ORDERS.filter(o => o.status === 'Hazırlanıyor').length;
    document.getElementById('pending-orders-count').innerText = pending;
}

// --- Products Logic ---
async function fetchProducts() {
    const res = await fetch('/api/products'); // DB fetch
    PRODUCTS = await res.json();
}

async function loadProducts() {
    await fetchProducts();
    const tbody = document.getElementById('products-table-body');
    tbody.innerHTML = '';

    PRODUCTS.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td><img src="${p.image}" class="table-img" onerror="this.src='/images/placeholder.png'"></td>
            <td>${p.name}</td>
            <td>${p.price} TL</td>
            <td>${p.stock}</td>
            <td><span class="badge ${p.is_active ? 'badge-success' : 'badge-danger'}">${p.is_active ? 'Aktif' : 'Pasif'}</span></td>
            <td>
                <i class="fas fa-edit action-btn" onclick="openEditProduct(${p.id})"></i>
                <i class="fas fa-trash action-btn delete-btn" onclick="deleteProduct(${p.id})"></i>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Global scope for onclick
window.openEditProduct = (id) => {
    const p = PRODUCTS.find(x => x.id === id);
    if (!p) return;

    document.getElementById('modalTitle').innerText = 'Ürün Düzenle';
    document.getElementById('productId').value = p.id;
    document.getElementById('pName').value = p.name;
    document.getElementById('pPrice').value = p.price;
    document.getElementById('pCategory').value = p.category;
    document.getElementById('pImage').value = p.image;
    document.getElementById('pDesc').value = p.description;

    document.getElementById('productModal').style.display = 'block';
};

window.deleteProduct = async (id) => {
    if (!confirm('Bu ürünü silmek istediğinize emin misiniz?')) return;

    const res = await fetch(`/api/products/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadProducts(); // Reload
    } else {
        alert('Silme işlemi başarısız');
    }
};

document.getElementById('addProductBtn').addEventListener('click', () => {
    document.getElementById('modalTitle').innerText = 'Yeni Ürün';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    document.getElementById('productModal').style.display = 'block';
});

document.getElementById('productForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const id = document.getElementById('productId').value;
    const data = {
        name: document.getElementById('pName').value,
        price: parseFloat(document.getElementById('pPrice').value),
        category: document.getElementById('pCategory').value,
        image: document.getElementById('pImage').value,
        description: document.getElementById('pDesc').value,
        stock: 100 // Default stock logic
    };

    let res;
    if (id) {
        // Update
        res = await fetch(`/api/products/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    } else {
        // Create
        res = await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    }

    if (res.ok) {
        document.getElementById('productModal').style.display = 'none';
        loadProducts();
    } else {
        alert('İşlem başarısız');
    }
});

// --- Orders Logic ---
async function fetchOrders() {
    const res = await fetch('/api/admin/orders');
    if (res.ok) ORDERS = await res.json();
}

async function loadOrders() {
    await fetchOrders();
    const tbody = document.getElementById('orders-table-body');
    tbody.innerHTML = '';

    ORDERS.forEach(o => {
        const tr = document.createElement('tr');
        const date = new Date(o.created_at).toLocaleDateString('tr-TR');
        tr.innerHTML = `
            <td>#${o.id}</td>
            <td>${date}</td>
            <td>${o.user_email || 'Bilinmiyor'}</td>
            <td>${o.total_amount} TL</td>
            <td><span class="badge badge-warning">${o.status}</span></td>
            <td><button class="btn-sm" onclick="viewOrder(${o.id})">Görüntüle</button></td>
        `;
        tbody.appendChild(tr);
    });
}

window.viewOrder = (id) => {
    const order = ORDERS.find(x => x.id === id);
    if (!order) return;

    document.getElementById('orderDetailId').innerText = order.id;
    document.getElementById('orderStatusSelect').value = order.status;

    // Items
    const list = document.getElementById('orderItemsList');
    list.innerHTML = order.items.map(item => `
        <div style="display:flex; justify-content:space-between; padding:5px; border-bottom:1px solid #eee;">
            <span>${item.product_name} x${item.quantity}</span>
            <span>${item.price_at_purchase} TL</span>
        </div>
    `).join('');

    // Bind Update Button
    document.getElementById('updateStatusBtn').onclick = async () => {
        const newStatus = document.getElementById('orderStatusSelect').value;
        const res = await fetch(`/api/admin/orders/${order.id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        if (res.ok) {
            document.getElementById('orderModal').style.display = 'none';
            loadOrders();
        } else {
            alert('Güncelleme başarısız');
        }
    };

    document.getElementById('orderModal').style.display = 'block';
};

// --- Modal Utilities ---
function setupModals() {
    const modals = document.querySelectorAll('.modal');
    const closes = document.querySelectorAll('.close-modal');

    closes.forEach(span => {
        span.onclick = () => {
            modals.forEach(m => m.style.display = 'none');
        };
    });

    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
}
