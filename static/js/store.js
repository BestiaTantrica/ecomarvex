// Estado del Carrito y Catálogo
let cart = JSON.parse(localStorage.getItem('dropship_cart') || '[]');
let catalogProducts = [];
let currentModalProduct = null;

document.addEventListener('DOMContentLoaded', () => {
  initProductsCache();
  updateCartBadge();
  setupSearch();
  checkUrlParams();
});

function initProductsCache() {
  const el = document.getElementById('productsCatalogData');
  if (el) {
    try {
      catalogProducts = JSON.parse(el.textContent);
    } catch (e) {
      console.error('Error parsing products data', e);
    }
  }
}

function saveCart() {
  localStorage.setItem('dropship_cart', JSON.stringify(cart));
  updateCartBadge();
  renderCartDrawer();
}

function updateCartBadge() {
  const count = cart.reduce((acc, item) => acc + item.quantity, 0);
  const badge = document.getElementById('cartCount');
  if (badge) badge.innerText = count;

  const mobileBar = document.getElementById('mobileCartBar');
  const mobileCount = document.getElementById('mobileCartCount');
  const mobileTotal = document.getElementById('mobileCartTotal');
  if (mobileBar) {
    if (count > 0) {
      const subtotal = cart.reduce((acc, i) => acc + (i.price * i.quantity), 0);
      if (mobileCount) mobileCount.innerText = count;
      if (mobileTotal) mobileTotal.innerText = `$${subtotal.toLocaleString('es-AR')}`;
      mobileBar.classList.add('visible');
    } else {
      mobileBar.classList.remove('visible');
    }
  }
}

function addToCart(id, title, price, image, origin = 'CABA / GBA', supplier = 'Dropsheable Mayorista') {
  const existing = cart.find(item => item.id === id);
  if (existing) {
    existing.quantity += 1;
    if (!existing.origin) existing.origin = origin;
    if (!existing.supplier) existing.supplier = supplier;
  } else {
    cart.push({ id, title, price, image, origin, supplier, quantity: 1 });
  }
  saveCart();
  
  // Abrir carrito y dar feedback
  const drawer = document.getElementById('cartDrawer');
  const overlay = document.getElementById('cartOverlay');
  if (drawer && !drawer.classList.contains('open')) {
    drawer.classList.add('open');
    overlay.classList.add('open');
  }
}

function updateQuantity(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;
  
  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter(i => i.id !== id);
  }
  saveCart();
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  saveCart();
}

function toggleCart() {
  const drawer = document.getElementById('cartDrawer');
  const overlay = document.getElementById('cartOverlay');
  drawer.classList.toggle('open');
  overlay.classList.toggle('open');
  if (drawer.classList.contains('open')) {
    renderCartDrawer();
  }
}

function renderCartDrawer() {
  const list = document.getElementById('cartItemsList');
  const alertEl = document.getElementById('cartLogisticsAlert');
  const subtotalEl = document.getElementById('cartSubtotal');
  const shippingEl = document.getElementById('cartShipping');
  const totalEl = document.getElementById('cartTotal');
  const checkoutBtn = document.getElementById('checkoutBtn');
  
  if (!list) return;

  if (cart.length === 0) {
    if (alertEl) alertEl.innerHTML = '';
    list.innerHTML = `
      <div class="cart-empty">
        <i class="fa-solid fa-basket-shopping"></i>
        <p>Tu carrito está vacío</p>
      </div>
    `;
    subtotalEl.innerText = '$0';
    if (shippingEl) shippingEl.innerText = '$0';
    totalEl.innerText = '$0';
    checkoutBtn.disabled = true;
    return;
  }

  let subtotal = 0;
  list.innerHTML = cart.map(item => {
    const lineTotal = item.price * item.quantity;
    subtotal += lineTotal;
    const itemOrigin = item.origin || 'CABA / GBA';
    return `
      <div class="cart-item">
        <img src="${item.image || 'https://via.placeholder.com/60'}" class="cart-item-img" alt="${item.title}">
        <div class="cart-item-info">
          <div class="cart-item-title">${item.title}</div>
          <div class="cart-item-price">$${item.price.toLocaleString('es-AR')}</div>
          <small style="font-size:0.72rem; color:#64748b;"><i class="fa-solid fa-location-dot"></i> ${itemOrigin}</small>
        </div>
        <div class="cart-item-qty">
          <button class="qty-btn" onclick="updateQuantity(${item.id}, -1)">-</button>
          <span>${item.quantity}</span>
          <button class="qty-btn" onclick="updateQuantity(${item.id}, 1)">+</button>
        </div>
        <button class="cart-item-remove" onclick="removeFromCart(${item.id})"><i class="fa-solid fa-trash-can"></i></button>
      </div>
    `;
  }).join('');

  // Análisis Logístico de Orígenes de Envío
  const cfg = window.STORE_CONFIG || { shippingFlatRate: 0, freeShippingMin: 0 };
  const origins = [...new Set(cart.map(i => i.origin || 'CABA / GBA'))];
  const packageCount = origins.length;

  if (alertEl) {
    if (cart.length === 1) {
      alertEl.innerHTML = `
        <div class="logistics-box unified">
          <i class="fa-solid fa-location-dot"></i>
          <div>
            <strong>Despacho Directo</strong>
            <p>Sale desde <strong>${origins[0]}</strong> directo a tu domicilio.</p>
          </div>
        </div>
      `;
    } else if (packageCount === 1) {
      alertEl.innerHTML = `
        <div class="logistics-box unified">
          <i class="fa-solid fa-boxes-packing"></i>
          <div>
            <strong>¡Mismo Depósito! (1 solo flete)</strong>
            <p>Todos tus productos salen de <strong>${origins[0]}</strong> en un único paquete.</p>
          </div>
        </div>
      `;
    } else {
      alertEl.innerHTML = `
        <div class="logistics-box multi">
          <i class="fa-solid fa-truck-ramp-box"></i>
          <div>
            <strong>Despacho Multi-Depósito (${packageCount} paquetes)</strong>
            <p>Tus productos salen de depósitos distintos: <strong>${origins.join(' y ')}</strong>. Llegarán en fletes separados.</p>
          </div>
        </div>
      `;
    }
  }

  // Cálculo automático de costo de envío
  let shippingCost = 0;
  if (cfg.shippingFlatRate > 0) {
    if (cfg.freeShippingMin > 0 && subtotal >= (cfg.freeShippingMin * packageCount)) {
      shippingCost = 0;
    } else {
      shippingCost = cfg.shippingFlatRate * packageCount;
    }
  }

  subtotalEl.innerText = `$${subtotal.toLocaleString('es-AR')}`;
  
  if (shippingEl) {
    if (cfg.shippingFlatRate > 0) {
      if (shippingCost === 0) {
        shippingEl.innerHTML = `<span style="color:#10b981; font-weight:700;">¡Bonificado!</span>`;
      } else {
        shippingEl.innerHTML = `$${shippingCost.toLocaleString('es-AR')} <small style="color:#64748b">(${packageCount} paquete${packageCount > 1 ? 's' : ''})</small>`;
      }
    } else {
      shippingEl.innerHTML = `<span style="color:#0284c7; font-weight:600; font-size:0.85rem;">A coordinar / comprador</span>`;
    }
  }

  const finalTotal = subtotal + shippingCost;
  totalEl.innerText = `$${finalTotal.toLocaleString('es-AR')}`;
  checkoutBtn.disabled = false;
}

// Filtro de categorías
function filterCategory(category) {
  document.querySelectorAll('.cat-pill').forEach(btn => {
    btn.classList.toggle('active', btn.innerText === category || (category === 'Todos' && btn.innerText.includes('Todos')));
  });

  document.querySelectorAll('.product-card').forEach(card => {
    const cardCat = card.getAttribute('data-category');
    if (category === 'Todos' || cardCat === category) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// Búsqueda en vivo
function setupSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;
  input.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.product-card').forEach(card => {
      const title = card.getAttribute('data-title');
      if (title.includes(q)) {
        card.style.display = 'flex';
      } else {
        card.style.display = 'none';
      }
    });
  });
}

function openCheckoutModal() {
  if (cart.length === 0) return;
  toggleCart(); // Cierra el drawer
  updateCheckoutPaymentSummary();
  document.getElementById('checkoutModal').classList.add('open');
}

function updateCheckoutPaymentSummary() {
  if (cart.length === 0) return;
  const subtotal = cart.reduce((acc, it) => acc + (it.price * it.quantity), 0);
  const cfg = window.STORE_CONFIG || { shippingFlatRate: 0, freeShippingMin: 80000, bankTransferDiscountPct: 10 };
  const origins = [...new Set(cart.map(i => i.origin || 'CABA / GBA'))];
  const packageCount = origins.length;

  let shippingCost = 0;
  if (cfg.shippingFlatRate > 0) {
    if (cfg.freeShippingMin > 0 && subtotal >= (cfg.freeShippingMin * packageCount)) {
      shippingCost = 0;
    } else {
      shippingCost = cfg.shippingFlatRate * packageCount;
    }
  }

  const payMethodInput = document.querySelector('input[name="payMethod"]:checked');
  const payMethod = payMethodInput ? payMethodInput.value : 'mercadopago';

  let discountAmount = 0;
  if (payMethod === 'transferencia') {
    const discountPct = cfg.bankTransferDiscountPct || 10;
    discountAmount = Math.round(subtotal * (discountPct / 100));
  }

  const finalTotal = Math.max(0, subtotal - discountAmount + shippingCost);

  const subtotalEl = document.getElementById('checkoutSubtotal');
  const discountRowEl = document.getElementById('checkoutDiscountRow');
  const discountEl = document.getElementById('checkoutDiscount');
  const shippingEl = document.getElementById('checkoutShipping');
  const totalEl = document.getElementById('checkoutTotal');
  const modalTotalEl = document.getElementById('modalTotal');

  if (subtotalEl) subtotalEl.innerText = `$${subtotal.toLocaleString('es-AR')}`;
  
  if (discountRowEl && discountEl) {
    if (discountAmount > 0) {
      discountRowEl.style.display = 'flex';
      discountEl.innerText = `-$${discountAmount.toLocaleString('es-AR')}`;
    } else {
      discountRowEl.style.display = 'none';
    }
  }

  if (shippingEl) {
    if (shippingCost === 0) {
      shippingEl.innerHTML = `<span style="color:#10b981; font-weight:700;">¡Bonificado!</span>`;
    } else {
      shippingEl.innerHTML = `$${shippingCost.toLocaleString('es-AR')} ${packageCount > 1 ? `<small style="color:#64748b">(${packageCount} paq.)</small>` : ''}`;
    }
  }

  if (totalEl) totalEl.innerText = `$${finalTotal.toLocaleString('es-AR')}`;
  if (modalTotalEl) modalTotalEl.innerText = `$${finalTotal.toLocaleString('es-AR')}`;
}

function closeCheckoutModal() {
  document.getElementById('checkoutModal').classList.remove('open');
}

async function submitOrder(e) {
  e.preventDefault();
  const btn = document.getElementById('submitOrderBtn');
  btn.disabled = true;
  btn.innerText = 'Procesando pedido...';

  const payload = {
    customer_name: document.getElementById('custName').value,
    customer_phone: document.getElementById('custPhone').value,
    customer_email: document.getElementById('custEmail').value,
    shipping_address: document.getElementById('custAddress').value,
    shipping_city: document.getElementById('custCity').value,
    shipping_province: document.getElementById('custProvince').value,
    shipping_postal_code: document.getElementById('custZip').value,
    payment_method: document.querySelector('input[name="payMethod"]:checked').value,
    notes: document.getElementById('orderNotes').value,
    items: cart.map(it => ({ product_id: it.id, quantity: it.quantity }))
  };

  try {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.detail || 'Error procesando la orden.');
      btn.disabled = false;
      btn.innerText = 'Confirmar y Pagar';
      return;
    }

    // Vaciar carrito
    cart = [];
    saveCart();
    closeCheckoutModal();

    // Mostrar modal de éxito según medio de pago
    showSuccessModal(data);
  } catch (err) {
    alert('Error de conexión con el servidor.');
    btn.disabled = false;
    btn.innerText = 'Confirmar y Pagar';
  }
}

function showSuccessModal(data) {
  const modal = document.getElementById('successModal');
  const codeEl = document.getElementById('successCode');
  const titleEl = document.getElementById('successTitle');
  const msgEl = document.getElementById('successMessage');
  const actionEl = document.getElementById('successAction');

  codeEl.innerText = data.order_code;

  if (data.payment_method === 'mercadopago' && data.mp_init_point) {
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&margin=1&data=${encodeURIComponent(data.mp_init_point)}`;
    titleEl.innerText = '¡Pedido Registrado con Éxito!';
    msgEl.innerText = 'Podés abonar al instante mediante Mercado Pago (Tarjetas, Débito, Cuotas o Dinero en Cuenta):';
    actionEl.innerHTML = `
      <div class="payment-qr-wrap mp-qr">
        <img src="${qrUrl}" alt="QR Mercado Pago" class="payment-qr-img" loading="lazy">
        <div class="payment-qr-title" style="color:#0284c7;"><i class="fa-solid fa-qrcode"></i> QR Mercado Pago</div>
        <p class="payment-qr-hint">Escaneá con tu celular o con la app de Mercado Pago para pagar con tarjeta, cuotas o saldo.</p>
      </div>
      <a href="${data.mp_init_point}" class="btn-primary-link" target="_blank" style="margin-top:8px;">
        <i class="fa-solid fa-credit-card"></i> Pagar con Mercado Pago en esta pantalla
      </a>
    `;
  } else if (data.payment_method === 'whatsapp' && data.whatsapp_url) {
    titleEl.innerText = '¡Pedido Casi Listo!';
    msgEl.innerText = 'Haz clic para enviar el detalle de tu orden por WhatsApp y coordinar el despacho:';
    actionEl.innerHTML = `
      <a href="${data.whatsapp_url}" class="btn-whatsapp-link" target="_blank">
        <i class="fa-brands fa-whatsapp"></i> Enviar Pedido a WhatsApp
      </a>
    `;
  } else if (data.payment_method === 'transferencia' && data.bank_info) {
    const finalAmount = data.bank_info.final_amount || data.total;
    const alias = data.bank_info.bank_alias || 'vida.rucula';
    const cbu = data.bank_info.bank_cbu || '0000003100017567089887';
    const holder = data.bank_info.bank_holder || 'Tomas Reis';
    const bank = data.bank_info.bank_name || 'Mercado Pago';
    const phone = (window.STORE_CONFIG && window.STORE_CONFIG.whatsappPhone) || '5491100000000';
    const waText = encodeURIComponent(`¡Hola! Ya realicé la transferencia de mi orden ${data.order_code} por un total de $${finalAmount.toLocaleString('es-AR')}. Adjunto el comprobante.`);
    const transferQrData = `0000003100017567089887`;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&margin=1&data=${encodeURIComponent(transferQrData)}`;

    titleEl.innerText = '¡Pedido Registrado con Éxito!';
    msgEl.innerHTML = `Tenés un <strong>10% OFF bonificado</strong> por abonar con Transferencia Directa.`;
    
    actionEl.innerHTML = `
      <div class="transfer-payment-details">
        <div class="transfer-amount-highlight">
          <span>Total con 10% OFF aplicado:</span>
          <h3>$${finalAmount.toLocaleString('es-AR')}</h3>
        </div>
        <div class="bank-card-data">
          <div class="bank-row">
            <span>Banco / Entidad:</span>
            <strong>${bank}</strong>
          </div>
          <div class="bank-row">
            <span>Titular:</span>
            <strong>${holder}</strong>
          </div>
          <div class="bank-row alias-row">
            <div>
              <span style="font-size:0.75rem; color:#64748b; display:block;">ALIAS DE PAGO:</span>
              <span class="alias-pill">${alias}</span>
            </div>
            <button type="button" class="btn-copy-alias" onclick="copyAlias('${alias}', this)">
              <i class="fa-solid fa-copy"></i> Copiar Alias
            </button>
          </div>
          <div class="bank-row" style="margin-top:6px; font-size:0.82rem;">
            <span>CBU / CVU:</span>
            <code>${cbu}</code>
          </div>
        </div>

        <!-- QR de Transferencia Bancaria Directa -->
        <div class="payment-qr-wrap transfer-qr">
          <img src="${qrUrl}" alt="QR Transferencia Directa" class="payment-qr-img" loading="lazy">
          <div class="payment-qr-title" style="color:#15803d;"><i class="fa-solid fa-qrcode"></i> QR Transferencia Directa</div>
          <p class="payment-qr-hint">Escaneá desde tu celular con cualquier app bancaria o billetera virtual (Mercado Pago, Cuenta DNI, BNA+, Ualá, etc.).</p>
        </div>

        <p class="transfer-notice">
          <i class="fa-solid fa-circle-info"></i> Realizá la transferencia desde tu homebanking o app favorita y envianos el comprobante por WhatsApp para despachar tu pedido.
        </p>
        <a href="https://wa.me/${phone}?text=${waText}" class="btn-whatsapp-comprobante" target="_blank">
          <i class="fa-brands fa-whatsapp"></i> Enviar Comprobante por WhatsApp
        </a>
      </div>
    `;
  } else {
    titleEl.innerText = '¡Pedido Recibido!';
    msgEl.innerText = 'Nos pondremos en contacto contigo a la brevedad para coordinar la entrega.';
    actionEl.innerHTML = '';
  }

  modal.classList.add('open');
}

function closeSuccessModal() {
  document.getElementById('successModal').classList.remove('open');
}

function checkUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const successOrder = params.get('order_success');
  if (successOrder) {
    alert(`¡Gracias por tu pago! Tu orden ${successOrder} fue aprobada con éxito.`);
    window.history.replaceState({}, document.title, "/");
  }
  const prodId = params.get('producto') || params.get('p');
  if (prodId) {
    openProductModal(parseInt(prodId));
  }
}

// ==========================================
// CONTROLADOR DEL MODAL DE DETALLE DE PRODUCTO
// ==========================================
async function openProductModal(productId) {
  let p = catalogProducts.find(item => item.id === productId);
  if (!p) {
    try {
      const res = await fetch(`/api/products/${productId}`);
      if (res.ok) {
        p = await res.json();
      }
    } catch (e) {
      console.error(e);
    }
  }
  if (!p) return;

  currentModalProduct = p;

  const modal = document.getElementById('productModal');
  const mainImg = document.getElementById('modalMainImg');
  const catBadge = document.getElementById('modalCatBadge');
  const thumbsBar = document.getElementById('modalThumbnails');
  const originTag = document.getElementById('modalOriginTag');
  const dispatchTag = document.getElementById('modalDispatchTag');
  const titleEl = document.getElementById('modalTitle');
  const supplierEl = document.getElementById('modalSupplierName');
  const skuEl = document.getElementById('modalSku');
  const oldPriceEl = document.getElementById('modalOldPrice');
  const salePriceEl = document.getElementById('modalSalePrice');
  const discountBadge = document.getElementById('modalDiscountBadge');
  const qtyInput = document.getElementById('modalQtyInput');
  const fullDescEl = document.getElementById('modalFullDescription');
  const waBtn = document.getElementById('modalWhatsAppBtn');

  // Resetear cantidad a 1
  if (qtyInput) qtyInput.value = 1;

  // Galería de Imágenes
  let images = p.images || [];
  if ((!images || images.length === 0) && p.image_url) {
    images = [p.image_url];
  }
  if (mainImg) {
    mainImg.src = images.length > 0 ? images[0] : (p.image_url || '');
    mainImg.alt = p.title;
  }
  if (catBadge) catBadge.innerText = p.category || 'General';

  // Renderizar Miniaturas si hay más de 1 imagen
  if (thumbsBar) {
    if (images.length > 1) {
      thumbsBar.style.display = 'flex';
      thumbsBar.innerHTML = images.map((imgUrl, idx) => `
        <div class="thumb-item ${idx === 0 ? 'active' : ''}" onclick="setModalMainImage('${imgUrl.replace(/'/g, "\\'")}', this)">
          <img src="${imgUrl}" alt="Vista ${idx + 1}" loading="lazy">
        </div>
      `).join('');
    } else {
      thumbsBar.style.display = 'none';
      thumbsBar.innerHTML = '';
    }
  }

  // Textos y Logística
  if (originTag) originTag.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${p.shipping_origin || 'CABA / GBA'}`;
  if (dispatchTag) dispatchTag.innerHTML = `<i class="fa-solid fa-clock"></i> ${p.dispatch_time || '24-48 hs hábiles'}`;
  if (titleEl) titleEl.innerText = p.title;
  if (supplierEl) supplierEl.innerText = p.supplier_name || 'Dropsheable Mayorista';
  if (skuEl) skuEl.innerText = `SKU: ${p.supplier_sku || 'DSH-' + p.id}`;

  // Precios y Descuento
  const salePrice = p.sale_price || 0;
  const oldPrice = p.discount_price && p.discount_price > salePrice ? p.discount_price : Math.round(salePrice * 1.2);
  if (salePriceEl) salePriceEl.innerText = `$${salePrice.toLocaleString('es-AR')}`;

  const transferPrice = Math.round(salePrice * 0.90);
  const modalTransferPriceEl = document.getElementById('modalTransferPrice');
  if (modalTransferPriceEl) {
    modalTransferPriceEl.innerText = transferPrice.toLocaleString('es-AR');
  }

  if (oldPrice > salePrice) {
    if (oldPriceEl) {
      oldPriceEl.innerText = `$${Math.round(oldPrice).toLocaleString('es-AR')}`;
      oldPriceEl.style.display = 'inline';
    }
    if (discountBadge) {
      const discountPct = Math.round(((oldPrice - salePrice) / oldPrice) * 100);
      discountBadge.innerText = `${discountPct}% OFF`;
      discountBadge.style.display = 'inline-block';
    }
  } else {
    if (oldPriceEl) oldPriceEl.style.display = 'none';
    if (discountBadge) discountBadge.style.display = 'none';
  }

  // Descripción Completa preservando saltos de línea y estructura
  if (fullDescEl) {
    const rawDesc = p.description || 'Este producto cuenta con garantía de fábrica y despacho directo.';
    const formattedDesc = escapeHtml(rawDesc).replace(/\r\n|\r|\n/g, '<br>');
    fullDescEl.innerHTML = formattedDesc;
  }

  // Botón directo a WhatsApp para consultar
  if (waBtn) {
    const phone = (window.STORE_CONFIG && window.STORE_CONFIG.whatsappPhone) || '5491100000000';
    const text = encodeURIComponent(`¡Hola! Quería consultar por el producto "${p.title}" ($${salePrice.toLocaleString('es-AR')}) que vi en EcoMarvex.`);
    waBtn.href = `https://wa.me/${phone}?text=${text}`;
  }

  // Abrir Modal
  if (modal) modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function setModalMainImage(url, thumbEl) {
  const mainImg = document.getElementById('modalMainImg');
  if (mainImg) mainImg.src = url;
  document.querySelectorAll('.thumb-item').forEach(el => el.classList.remove('active'));
  if (thumbEl) thumbEl.classList.add('active');
}

function closeProductModal(event) {
  if (event && event.target && !event.target.classList.contains('product-modal-overlay') && !event.target.closest('.close-product-modal-btn')) {
    return;
  }
  const modal = document.getElementById('productModal');
  if (modal) modal.classList.remove('open');
  document.body.style.overflow = '';
}

function changeModalQty(delta) {
  const input = document.getElementById('modalQtyInput');
  if (!input) return;
  let val = parseInt(input.value) || 1;
  val = Math.max(1, Math.min(99, val + delta));
  input.value = val;
}

function addModalProductToCart() {
  if (!currentModalProduct) return;
  const qtyInput = document.getElementById('modalQtyInput');
  const qty = parseInt(qtyInput ? qtyInput.value : 1) || 1;
  
  for (let i = 0; i < qty; i++) {
    addToCart(
      currentModalProduct.id,
      currentModalProduct.title,
      currentModalProduct.sale_price,
      currentModalProduct.image_url,
      currentModalProduct.shipping_origin || 'CABA / GBA',
      currentModalProduct.supplier_name || 'Dropsheable Mayorista'
    );
  }
  
  closeProductModal();
}

function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}

// ==========================================
// UTILIDADES PARA COPIAR ALIAS
// ==========================================
function copyAlias(alias, btn) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(alias).then(() => {
      btnFeedback(btn);
    }).catch(() => {
      fallbackCopy(alias, btn);
    });
  } else {
    fallbackCopy(alias, btn);
  }
}

function fallbackCopy(text, btn) {
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    btnFeedback(btn);
  } catch (err) {
    alert('Alias: ' + text);
  }
  document.body.removeChild(ta);
}

function btnFeedback(btn) {
  if (!btn) return;
  const original = btn.innerHTML;
  btn.innerHTML = `<i class="fa-solid fa-check"></i> ¡Copiado!`;
  btn.style.background = '#059669';
  setTimeout(() => {
    btn.innerHTML = original;
    btn.style.background = '';
  }, 2500);
}

