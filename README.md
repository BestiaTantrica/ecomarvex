# 🛍️ EcoMarvex | Plataforma E-commerce Dropshipping Argentina

Plataforma integral de comercio electrónico de alta velocidad y arquitectura ligera (<150 MB RAM) diseñada para operar en el ecosistema de **Dropshipping en Argentina** (Dropsheable, Dropi, proveedores mayoristas locales), con **atención automática por WhatsApp 24/7 con Inteligencia Artificial** y pasarela de cobros con **Mercado Pago** y **Transferencias Bancarias (0% comisión)**.

---

## 🌟 Características Principales

### 🛒 1. Tienda Online (Storefront)
* **Diseño Moderno & Ultra-Rápido:** Interfaz limpia construida con HTML5 semántico, CSS moderno y JavaScript Vanilla nativo (sin dependencias pesadas ni frameworks lentos).
* **Inteligencia Logística Multi-Depósito:**
  * Detección automática del depósito de origen de cada producto (`CABA / GBA`, `Córdoba`, `Rosario`, etc.).
  * Carrito inteligente: Alerta al comprador si su pedido sale de un único depósito (*Envío Unificado*) o si proviene de múltiples mayoristas (*Despacho en paquetes separados*).
  * Cálculo dinámico de fletes con regla de envío bonificado/gratis configurable desde el panel.
* **Carrito y Checkout Dinámico:** Soporte de compra rápida para cobro vía **Mercado Pago**, **Transferencia Bancaria** o **Coordinación directa por WhatsApp**.

### 📱 2. Bot de WhatsApp 24/7 con Inteligencia Artificial
* **Conexión Directa con tu propio número:** Integración vía socket liviano (`@whiskeysockets/baileys`) sin costo de Meta API oficial.
* **Vinculación en 1 Clic con Código QR:** Escaneo directo desde *Dispositivos Vinculados* de WhatsApp en el panel administrador.
* **Auto-Respuesta Humanizada:**
  * Simulación de tipeo (*"escribiendo..."*) con delay configurable de 3.5s a 5.5s para un trato 100% natural.
  * Respuestas contextualizadas con el catálogo de productos, tiempos de entrega y datos de transferencia (Alias/CBU).

### 🪄 3. Asistente & Marketing con IA (Gemini)
* **Creador de Publicaciones Virales:** Generador de guiones de 30 segundos, ganchos (*hooks*) para TikTok/Reels y copys con hashtags para Instagram.
* **Cascada Resiliente de Modelos & Rotación de Claves:**
  * Rotación automática entre múltiples claves de API para evitar límites de cuota diaria.
  * Fallback en cascada entre modelos: `gemini-3.5-flash-lite` ➔ `gemini-3.5-flash` ➔ `gemini-2.5-flash`.
* **Asesor Experto en Dropshipping:** Análisis de nichos rentables y márgenes seguros.

### 🔌 4. Dropsheable Argentina Hub
* **Gestión de Credenciales Seguras:** Almacenamiento seguro de `API Key` y `API Secret` de Dropsheable.
* **Buscador & Analizador de Proveedores y Productos:** Evaluación de productos ganadores, depósitos de origen y fletes mayoristas de Andreani y Correo Argentino.

---

## 🏗️ Arquitectura Técnica

```
ecomarvex/
├── main.py                 # Servidor principal FastAPI y endpoints de negocio
├── database.py             # Capa de datos SQLite y migraciones automáticas
├── ai_service.py           # Motor de IA (Gemini SDK con rotación y fallback)
├── requirements.txt        # Dependencias Python
├── deploy_to_oci1.sh       # Script de despliegue automatizado a Oracle Cloud
├── templates/
│   ├── index.html          # Vista pública de la tienda (Catálogo + Carrito + Checkout)
│   └── admin.html          # Panel de administración, métricas y configuración
├── static/
│   ├── css/style.css       # Sistema de diseño y estilos responsive
│   └── js/
│       ├── store.js        # Lógica del cliente, carrito y cálculo de envíos
│       └── admin.js        # Lógica del panel de administración
└── whatsapp_bridge/
    ├── index.js            # Daemon Node.js / Baileys (Bridge de WhatsApp 24/7)
    └── package.json        # Dependencias de Baileys, QRCode y Pino
```

---

## 🚀 Despliegue en Servidor (Oracle Cloud / Ubuntu)

El proyecto incluye un script de despliegue desatendido (`deploy_to_oci1.sh`):

```bash
chmod +x deploy_to_oci1.sh
./deploy_to_oci1.sh
```

El script se encarga automáticamente de:
1. Sincronizar archivos vía `rsync` hacia el servidor remoto.
2. Configurar el entorno virtual Python y actualizar dependencias.
3. Configurar el demonio Node.js de WhatsApp.
4. Crear y recargar los servicios de `systemd` (`tienda.service` y `whatsapp-bot.service`).
5. Configurar Nginx con proxy reverso y certificados SSL de Let's Encrypt.

---

## 🔒 Seguridad y Privacidad
* Las claves de API y secretos se almacenan exclusivamente en la base de datos local SQLite (`data/tienda.db`) en el servidor de producción.
* El archivo `.gitignore` previene la subida accidental de llaves privadas SSH, bases de datos o tokens de sesión de WhatsApp.

---

© 2026 EcoMarvex. Desarrollado para comercio electrónico de alto rendimiento.
