import os
import json
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

def generate_whatsapp_reply(customer_message: str, product_title: Optional[str], settings: Dict[str, Any]) -> Dict[str, Any]:
    """Drafts an Argentine, friendly, and persuasive WhatsApp reply."""
    store_name = settings.get("store_name", "EcoMarvex")
    bank_alias = settings.get("bank_alias", "")
    bank_cbu = settings.get("bank_cbu", "")
    shipping_policy = settings.get("shipping_policy_text", "Envío a convenir / a cargo del comprador por Andreani o Correo Argentino")

    prompt = f"""
Eres el asistente de atención al cliente de la tienda online argentina "{store_name}" (ecomarvex.com).
Un cliente te escribió este mensaje por WhatsApp:
"{customer_message}"

{f'Producto consultado: {product_title}' if product_title else ''}
Datos de la tienda:
- Política de envíos: {shipping_policy}
- Datos bancarios si consulta para pagar por transferencia: Alias: {bank_alias} | CBU: {bank_cbu}
- Web oficial: https://ecomarvex.com

Instrucciones:
1. Responde con tono argentino cordial, cercano, educado y profesional (usa voseo natural: "Hola! Sí, tenemos disponible...", "Te comento...", "Podés comprarlo...").
2. Si pregunta por stock o envíos, aclara que despachamos a todo el país por correo y que el envío se coordina tras la compra.
3. Si pregunta cómo pagar, indícale que puede abonar con Mercado Pago (tarjetas/cuotas) o por Transferencia Bancaria directa con descuento.
4. Mantén la respuesta breve (máximo 3-4 párrafos cortos) con emojis adecuados para WhatsApp.

Devuelve solo el texto del mensaje listo para enviar por WhatsApp.
"""
    reply, model_used = execute_gemini_cascade(prompt, settings, is_json=False)
    return {"reply": reply, "model_used": model_used}

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
