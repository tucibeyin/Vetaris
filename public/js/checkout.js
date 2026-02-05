document.addEventListener('DOMContentLoaded', () => {
    loadCheckoutSummary();
});

// Load cart data
function loadCheckoutSummary() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const itemsContainer = document.getElementById('checkout-items');

    if (cart.length === 0) {
        alert('Sepetiniz boş! Anasayfaya yönlendiriliyorsunuz.');
        window.location.href = '/index.html';
        return;
    }

    let total = 0;
    itemsContainer.innerHTML = cart.map(item => {
        total += item.price * item.quantity;
        return `
            <div style="display:flex; align-items:center; margin-bottom:1rem; border-bottom:1px solid #f9f9f9; padding-bottom:0.5rem;">
                <img src="${item.image}" style="width:50px; height:50px; object-fit:contain; border-radius:4px; margin-right:1rem;">
                <div style="flex:1;">
                    <div style="font-weight:600; font-size:0.9rem;">${item.name}</div>
                    <div style="font-size:0.8rem; color:#777;">${item.quantity} adet</div>
                </div>
                <div style="font-weight:600;">${(item.price * item.quantity).toFixed(2)} ₺</div>
            </div>
        `;
    }).join('');

    document.getElementById('summary-subtotal').innerText = total.toFixed(2) + ' ₺';
    document.getElementById('summary-total').innerText = total.toFixed(2) + ' ₺';
    document.getElementById('pay-amount').innerText = '(' + total.toFixed(2) + ' ₺)';
}

// Navigation Steps
const stepAddress = document.getElementById('step-address');
const stepPayment = document.getElementById('step-payment');

document.getElementById('addressForm').addEventListener('submit', (e) => {
    e.preventDefault();
    // Simple validation passed
    // Transition to Payment
    stepAddress.classList.add('hidden-step');
    stepPayment.classList.remove('hidden-step');
    window.scrollTo(0, 0);
});

window.goBackToAddress = () => {
    stepPayment.classList.add('hidden-step');
    stepAddress.classList.remove('hidden-step');
};

// Payment Form Formatting
window.formatCardNum = (input) => {
    let val = input.value.replace(/\D/g, '');
    val = val.replace(/(.{4})/g, '$1 ').trim();
    input.value = val;
    updateCardDisplay();
};

window.formatCardExp = (input) => {
    let val = input.value.replace(/\D/g, '');
    if (val.length >= 2) {
        val = val.substring(0, 2) + '/' + val.substring(2, 4);
    }
    input.value = val;
    updateCardDisplay();
};

window.updateCardDisplay = () => {
    const num = document.getElementById('card-num').value || '#### #### #### ####';
    const name = document.getElementById('card-name').value || 'AD SOYAD';
    const exp = document.getElementById('card-exp').value || 'MM/YY';

    document.getElementById('disp-card-num').innerText = num;
    document.getElementById('disp-card-name').innerText = name.toUpperCase();
    document.getElementById('disp-card-exp').innerText = exp;
};

// Payment Submission
document.getElementById('paymentForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Simulate Processing
    const loader = document.getElementById('loader');
    loader.style.display = 'flex';

    // Fake limit delay
    await new Promise(r => setTimeout(r, 2000));

    // Validating card (basic check)
    const cardNum = document.getElementById('card-num').value.replace(/\s/g, '');
    if (cardNum.length < 16) {
        loader.style.display = 'none';
        alert('Lütfen geçerli bir kart numarası giriniz.');
        return;
    }

    try {
        // Construct Order Data
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        const items = cart.map(i => ({ product_id: i.id, quantity: i.quantity }));

        // Call API
        const res = await fetch('/api/orders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items })
        });

        if (res.ok) {
            // Success
            localStorage.removeItem('cart'); // Clear cart
            loader.innerHTML = `
                <div class="loader-spinner" style="border-top-color: #28a745;"></div>
                <h3>Sipariş Alındı! 🎉</h3>
                <p>Hesabım sayfasına yönlendiriliyorsunuz...</p>
            `;
            setTimeout(() => {
                window.location.href = '/account.html';
            }, 2000);
        } else {
            const err = await res.json();
            throw new Error(err.error || 'Sipariş oluşturulamadı');
        }

    } catch (error) {
        loader.style.display = 'none';
        alert('Hata: ' + error.message);
        // If not auth, redirect
        if (error.message.includes('Giriş')) {
            window.location.href = '/login.html';
        }
    }
});
