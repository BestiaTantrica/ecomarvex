import os
import re
import json
import sqlite3
import logging
import requests
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("ai_service")

# Model fallback cascade
GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest"
]

def get_available_keys(settings: Dict[str, Any]) -> List[str]:
    """Collects all configured Gemini keys without duplicates."""
    keys = []
    
    # 1. Primary key from settings or env
    primary = settings.get("gemini_api_key", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
    if primary:
        for k in primary.replace("\n", ",").split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
                
    # 2. Backup key
    backup = settings.get("gemini_api_key_backup", "").strip() or os.getenv("GEMINI_API_KEY_BACKUP", "").strip()
    if backup:
        for k in backup.replace("\n", ",").split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
                
    return keys

def execute_gemini_cascade(prompt: str, settings: Dict[str, Any], is_json: bool = False) -> Tuple[str, str]:
    """
    Executes prompt across available keys and models in cascade order.
    Returns (response_text, model_used).
    """
    keys = get_available_keys(settings)
    if not keys:
        raise Exception("No hay ninguna Gemini API Key configurada. Agrega al menos una en Configuración.")

    errors = []
    
    for key in keys:
        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            try:
                res = requests.post(url, json=payload, timeout=18)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            return text, model
                    errors.append(f"Model {model}: respuesta vacía de Google")
                elif res.status_code == 429:
                    # Cuota excedida para esta key, probar con la siguiente key/modelo
                    errors.append(f"Key ...{key[-6:]} / {model}: Cuota excedida (429)")
                    break # Salta a la siguiente clave
                elif res.status_code == 404:
                    # Modelo en desuso o no disponible
                    errors.append(f"Model {model}: 404 No disponible")
                    continue # Prueba siguiente modelo
                else:
                    errors.append(f"Model {model}: HTTP {res.status_code}")
            except Exception as e:
                errors.append(f"Model {model}: error de conexión ({str(e)})")
                
    raise Exception(f"Todas las claves y modelos de IA fallaron. Detalles: {'; '.join(errors[:4])}")

def generate_social_content(product: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    """Generates viral social media pack for a product."""
    store_name = settings.get("store_name", "EcoMarvex")
    prompt = f"""
Eres el director de marketing digital de "{store_name}" (e-commerce argentino en ecomarvex.com).
Tu misión es crear una campaña viral para redes sociales (TikTok, Reels, Instagram) para vender este producto:

- Producto: {product.get('title')}
- Categoría: {product.get('category')}
- Precio de venta al público: ${product.get('sale_price', 0):,.0f} ARS
- Descripción: {product.get('description', '')}

Genera un JSON EXACTO con esta estructura:
{{
  "tiktok_hook": "Frase impactante de 3 segundos para captar la atención en TikTok o Instagram Reel",
  "tiktok_script": "Guión rápido de 30-45 segundos explicando qué mostrar en cámara y qué decir (paso a paso)",
  "instagram_caption": "Texto completo para el post de Instagram con emojis, beneficios del producto y llamada a comprar en ecomarvex.com (con cuotas y envíos a todo el país)",
  "hashtags": "8 a 10 hashtags virales (#EcoMarvex, #DropshippingArgentina, #Ofertas, etc.)",
  "selling_points": ["Beneficio clave 1", "Beneficio clave 2", "Beneficio clave 3"]
}}
Responde ÚNICAMENTE con el objeto JSON puro, sin bloques markdown de código.
"""
    raw_text, model_used = execute_gemini_cascade(prompt, settings, is_json=True)
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
    if raw_text.endswith("```"):
        raw_text = raw_text.rsplit("\n", 1)[0]
    result = json.loads(raw_text.strip())
    result["model_used"] = model_used
    return result

def get_catalog_context(customer_message: str, product_title: Optional[str] = None) -> str:
    """Dynamically queries the SQLite database for real-time prices, stock, and categories matching customer messages."""
    try:
        from database import get_connection
        conn = get_connection()
        c = conn.cursor()

        # 1. Si viene con título de producto explícito (ej: botón de la web)
        if product_title:
            c.execute(
                "SELECT title, sale_price, stock, category, shipping_origin, dispatch_time FROM products WHERE active = 1 AND title LIKE ? LIMIT 3",
                (f"%{product_title[:25]}%",)
            )
            rows = c.fetchall()
            if rows:
                conn.close()
                return "Producto consultado desde la web:\n" + "\n".join([
                    f"- {r['title']} | Precio: ${r['sale_price']:,.0f} ARS | Stock: {r['stock']} un. | Despacho: {r['dispatch_time']} ({r['shipping_origin']})"
                    for r in rows
                ])

        # 2. Búsqueda por palabras clave del mensaje en la base de datos
        tokens = [t.strip().lower() for t in re.split(r"\W+", customer_message) if len(t.strip()) >= 3]
        ignore_words = {"hola", "buenas", "tardes", "noches", "dias", "precio", "cuanto", "sale", "tenes", "tienen", "stock", "envio", "envios", "hacen", "puedo", "comprar", "donde", "estan", "gratis", "costo", "pago", "cuotas", "para", "como", "esta", "este"}
        search_tokens = [t for t in tokens if t not in ignore_words]

        matches = []
        if search_tokens:
            clause = " OR ".join(["title LIKE ? OR category LIKE ? OR description LIKE ?" for _ in search_tokens[:4]])
            query = f"SELECT title, sale_price, stock, category, shipping_origin, dispatch_time FROM products WHERE active = 1 AND ({clause}) LIMIT 6"
            params = []
            for t in search_tokens[:4]:
                params.extend([f"%{t}%", f"%{t}%", f"%{t}%"])
            c.execute(query, params)
            matches = c.fetchall()

        if matches:
            res = "Productos reales encontrados en la tienda para esta consulta:\n"
            for r in matches:
                res += f"- {r['title']} | Precio: ${r['sale_price']:,.0f} ARS | Stock: {r['stock']} un. | Despacho: {r['dispatch_time']} ({r['shipping_origin']})\n"
            conn.close()
            return res
        else:
            # Resumen general de categorías activas para cuando preguntan genéricamente
            c.execute("SELECT category, count(*) as count, min(sale_price) as min_p FROM products WHERE active = 1 GROUP BY category")
            cats = c.fetchall()
            conn.close()
            if cats:
                return "Categorías y rubros activos actualmente en EcoMarvex:\n" + "\n".join([
                    f"- {r['category']} (desde ${r['min_p']:,.0f} ARS)" for r in cats
                ])
            return ""
    except Exception as e:
        logger.warning(f"Error extrayendo contexto de catálogo para WhatsApp: {e}")
        return ""

def generate_whatsapp_reply(customer_message: str, product_title: Optional[str], settings: Dict[str, Any]) -> Dict[str, Any]:
    """Drafts an Argentine, friendly, and persuasive WhatsApp reply ONLY for legitimate store customers.
    Detects personal/family messages and outputs IGNORAR to protect the seller's personal life.
    Armed with real-time catalog prices, stock, shipping thresholds, and bank details."""
    store_name = settings.get("store_name", "EcoMarvex")
    bank_alias = settings.get("bank_alias", "vida.rucula")
    bank_cbu = settings.get("bank_cbu", "0000003100017567089887")
    bank_holder = settings.get("bank_holder", "Tomas Reis")
    bank_name = settings.get("bank_name", "Mercado Pago")
    
    try:
        free_shipping_val = float(settings.get("free_shipping_min") or 80000)
    except Exception:
        free_shipping_val = 80000.0
    if free_shipping_val <= 0:
        free_shipping_val = 80000.0

    try:
        transfer_discount_pct = float(settings.get("bank_transfer_discount_pct") or 10)
    except Exception:
        transfer_discount_pct = 10.0

    shipping_policy = settings.get("shipping_policy_text", "Envíos directos a todo el país por Andreani o Correo Argentino con código de seguimiento")
    catalog_context = get_catalog_context(customer_message, product_title)

    prompt = f"""
Eres el asistente virtual oficial de atención al cliente de la tienda online argentina "{store_name}" (ecomarvex.com).
Tu trabajo es atender con calidez, exactitud y tono argentino ÚNICAMENTE consultas comerciales de clientes de la tienda.
El dueño del teléfono usa este mismo número para su vida personal (familia, amigos, conocidos).

Un usuario te escribió este mensaje por WhatsApp:
"{customer_message}"

{f'Producto consultado desde la web: {product_title}' if product_title else ''}

INFORMACIÓN COMERCIAL, LOGÍSTICA Y POLÍTICAS ACTUALIZADAS:
- ENVÍO GRATIS: Promoción activa de ¡ENVÍO GRATIS A TODO EL PAÍS! en carritos o compras que alcancen o superen los ${free_shipping_val:,.0f} ARS. Si la compra es menor, el envío se calcula a costo muy accesible según el código postal por Andreani o Correo Argentino.
- LOGÍSTICA Y DESPACHOS: Despachamos en 24-48 hs hábiles directamente desde los centros de distribución oficiales de cada fabricante (CABA / GBA) con embalaje seguro y código de seguimiento online.
- MEDIOS DE PAGO Y DESCUENTOS:
  1. Transferencia Bancaria Directa: ¡{transfer_discount_pct:.0f}% DE DESCUENTO INMEDIATO ({transfer_discount_pct:.0f}% OFF)! Alias: {bank_alias} | CBU: {bank_cbu} (Titular: {bank_holder}, {bank_name}). Menciona siempre este 10% OFF si el cliente pregunta por medios de pago, transferencias o descuentos.
  2. Tarjetas de crédito/débito y cuotas a través de la web con Mercado Pago.
- COMPRA ONLINE: Todo el catálogo se puede comprar directamente en https://ecomarvex.com con carrito inteligente y cálculo automático.

CATÁLOGO EN TIEMPO REAL (BASE DE DATOS EN VIVO):
{catalog_context if catalog_context else 'Catálogo multirubro: Veladores de diseño 3D, Perfumes Árabes importados, Cuidado personal, Indumentaria deportiva y Calzado.'}

INSTRUCCIÓN DE FILTRADO DE SEGURIDAD (CRÍTICA):
1. Analiza cuidadosamente la intención del mensaje:
   - ¿Es una consulta comercial de compra, catálogo, productos, precios, stock, envíos, formas de pago (CBU, alias, Mercado Pago) o pedidos (#ECO-...) de la tienda?
   - ¿O es un mensaje personal, familiar, cotidiano, informal de amigos o ajeno a la tienda (ej: "hola pa", "a qué hora venís", "¿viste el partido?", "¿compraste el pan?", "llamame", "te paso las fotos", saludos casuales, temas de trabajo ajenos)?

2. SI EL MENSAJE ES PERSONAL, FAMILIAR, CASUAL O NO TIENE NINGUNA RELACIÓN CON UNA COMPRA EN ECOMARVEX:
   Debes responder ÚNICAMENTE con la palabra: IGNORAR
   (Sin saludos, sin explicaciones, sin comillas, exactamente la palabra: IGNORAR)

3. SI Y SOLO SI ES UNA CONSULTA COMERCIAL O UN CLIENTE DE LA TIENDA:
   - Responde cordialmente con tono argentino (usa voseo natural: "Hola! Sí, tenemos disponible...", "Te comento...", "Podés comprarlo...", etc.).
   - Brinda los precios y stock exactos basados en el catálogo en tiempo real si aplican.
   - Si consultan por medios de pago o descuentos, destaca que pagando con Transferencia Bancaria Directa tienen un {transfer_discount_pct:.0f}% OFF inmediato.
   - Si consultan por envíos o si el producto vale cerca de ${free_shipping_val:,.0f}, recuérdale con entusiasmo que superando los ${free_shipping_val:,.0f} ARS el envío es 100% GRATIS a todo el país.
   - Mantén la respuesta breve (máximo 2-3 párrafos cortos) con emojis adecuados para WhatsApp.
   - Devuelve solo el texto del mensaje listo para enviar al cliente.
"""
    reply, model_used = execute_gemini_cascade(prompt, settings, is_json=False)
    cleaned = (reply or "").strip()
    if cleaned.upper() == "IGNORAR" or cleaned.upper().startswith("IGNORAR"):
        return {"reply": None, "ignored": True, "reason": "personal_or_unrelated", "model_used": model_used}

    return {"reply": cleaned, "ignored": False, "model_used": model_used}

# Directorio verificado de Proveedores Reales activos en Dropsheable Argentina
DROPSHEABLE_REAL_SUPPLIERS = """
Directorio de Proveedores Reales activos en Dropsheable (dropsheable.com.ar):
1. TecnoWholesale Argentina (CABA) - Especialidad: Auriculares TWS, Smartwatches, cargadores, accesorios celulares y gadgets. Despacho: 24hs.
2. Por Algo Paso (Ramos Mejía, GBA Oeste) - Especialidad: Lámparas de diseño, humidificadores, bazar y productos virales de TikTok/Instagram. Despacho: 24-48hs.
3. SUCHIN Autopartes (CABA / GBA) - Especialidad: Soportes de celular magnéticos para auto, infladores portátiles, accesorios vehiculares. Despacho: 24hs.
4. Sina Artículos del Hogar (CABA / GBA) - Especialidad: Pequeños electrodomésticos (freidoras sin aceite, pavas eléctricas, licuadoras), cocina. Despacho: 24-48hs.
5. MayoristaNet (CABA) - Especialidad: Electrónica de consumo masivo, parlantes Bluetooth, aros de luz, micrófonos. Despacho: 24hs.
6. Lumina (Ituzaingó, GBA Oeste) - Especialidad: Belleza, cuidado personal, cepillos secadores iónicos, perfiladoras. Despacho: 24-48hs.
7. Proveedora Insumos Médicos & Fit (CABA) - Especialidad: Masajeadores de percusión, tensiómetros, bienestar y fitness. Despacho: 24hs.
"""

def ask_dropshipping_advisor(question: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Provides direct, actionable advice on real Dropsheable suppliers, products, and operational steps."""
    prompt = f"""
Eres el asesor operativo y comercial de la tienda EcoMarvex (ecomarvex.com) con base en Argentina.
Conocimiento de proveedores reales en Dropsheable:
{DROPSHEABLE_REAL_SUPPLIERS}

Consulta del dueño de la tienda:
"{question}"

REGLAS ESTRICTAS DE RESPUESTA:
1. NADA DE TEXTO GENÉRICO NI INTRODUCCIONES LARGAS. Ve directamente al grano.
2. Si pregunta por productos o rubros, indica qué proveedor real de Dropsheable lo tiene, su ubicación de despacho y costo/precio sugerido aproximado.
3. Brinda pasos de acción concretos: qué buscar exactamente en dropsheable.com.ar y cómo proceder.
4. Mantén la respuesta breve (máximo 3 o 4 viñetas directas).
"""
    advice, model_used = execute_gemini_cascade(prompt, settings, is_json=False)
    return {"advice": advice, "model_used": model_used}

def analyze_dropsheable_query(mode: str, query: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes real products and suppliers for Dropsheable Argentina with concrete numbers and zero fluff."""
    prompt = f"""
Eres el analista de compras mayoristas de EcoMarvex (ecomarvex.com).
Conocimiento de proveedores reales en Dropsheable:
{DROPSHEABLE_REAL_SUPPLIERS}

Modo: {mode}
Consulta: "{query}"

REGLAS ESTRICTAS:
- Cero teoría o rellenos de consultoría. Solo datos concretos y orientación práctica inmediata.
- Detalla:
  1. Proveedor real sugerido en Dropsheable y zona de despacho (CABA / GBA).
  2. Rango de costo mayorista real vs. PVP sugerido en Argentina.
  3. Flete estimado (Andreani/Correo ~$6.500 ARS) y viabilidad de venderlo solo o en combo.
  4. Pasos exactos a dar en dropsheable.com.ar para vincularte con ese proveedor y sumarlo a tu catálogo.
- Máximo 4 secciones cortas y contundentes.
"""
    advice, model_used = execute_gemini_cascade(prompt, settings, is_json=False)
    return {"analysis": advice, "model_used": model_used}
