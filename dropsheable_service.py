import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_connection, get_settings

logger = logging.getLogger("dropsheable_service")

DROPSHEABLE_API_BASE = "https://dropsheable.com.ar/frontv2/api/v1"

def _make_request(endpoint: str, api_key: str, api_secret: str = "", method: str = "GET", data: Optional[dict] = None) -> Dict[str, Any]:
    url = f"{DROPSHEABLE_API_BASE}{endpoint}"
    headers = {
        "User-Agent": "EcoMarvex-Store/1.0",
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    if api_secret:
        headers["X-API-Secret"] = api_secret

    encoded_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            raw = res.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(raw)
            except Exception:
                return {"success": True, "raw": raw}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        logger.error(f"Dropsheable HTTP Error {e.code} on {endpoint}: {error_body}")
        try:
            parsed = json.loads(error_body)
            return {"success": False, "code": e.code, "error": parsed.get("error", f"HTTP {e.code}"), "detail": parsed}
        except Exception:
            return {"success": False, "code": e.code, "error": f"HTTP {e.code}: {error_body[:100]}"}
    except Exception as e:
        logger.error(f"Dropsheable Request Error on {endpoint}: {e}")
        return {"success": False, "error": str(e)}

def check_dropsheable_connection(api_key: Optional[str] = None, api_secret: Optional[str] = None) -> Dict[str, Any]:
    """Verifies live connection, account info, and active integration with Dropsheable."""
    if not api_key:
        settings = get_settings()
        api_key = settings.get("dropsheable_api_key", "").strip()
        api_secret = settings.get("dropsheable_api_secret", "").strip()

    if not api_key:
        return {
            "connected": False,
            "error": "No hay API Key de Dropsheable configurada.",
            "min_seller_id": None
        }

    status_res = _make_request("/status", api_key, api_secret)
    if not status_res.get("success"):
        return {
            "connected": False,
            "error": status_res.get("error", "Error al conectar con la API de Dropsheable"),
            "code": status_res.get("code")
        }

    # Fetch active integration and stats
    integ_res = _make_request("/integraciones", api_key, api_secret)
    stats_res = _make_request("/stats", api_key, api_secret)

    min_seller_id = None
    integration_info = None
    if integ_res.get("success") and integ_res.get("data", {}).get("integraciones"):
        first_integ = integ_res["data"]["integraciones"][0]
        min_seller_id = first_integ.get("MinSellerID")
        integration_info = {
            "id": first_integ.get("ID"),
            "plataforma": first_integ.get("Plataforma"),
            "nombre_tienda": first_integ.get("NombreTienda"),
            "estado": first_integ.get("Estado"),
            "fecha_creacion": first_integ.get("FechaCreacion")
        }

    stats = stats_res.get("data", {})

    return {
        "connected": True,
        "api_version": status_res.get("api_version", "v1"),
        "min_seller_id": min_seller_id or 4754,
        "integration": integration_info,
        "stats": {
            "productos_total": stats.get("productos", {}).get("total", 0),
            "productos_activos": stats.get("productos", {}).get("activos", 0),
            "pedidos_total": stats.get("pedidos", {}).get("total", 0),
            "pedidos_entregados": stats.get("pedidos", {}).get("entregados", 0)
        }
    }

def get_dropsheable_catalog(search: str = "", category: str = "", supplier_id: Optional[int] = None) -> Dict[str, Any]:
    """Retrieves live products from Dropsheable API or returns verified catalog."""
    settings = get_settings()
    api_key = settings.get("dropsheable_api_key", "").strip()
    api_secret = settings.get("dropsheable_api_secret", "").strip()

    endpoint = "/productos?activo=1&limite=100"
    if search:
        endpoint += f"&search={urllib.parse.quote(search)}"
    if supplier_id:
        endpoint += f"&proveedor={supplier_id}"

    live_res = _make_request(endpoint, api_key, api_secret)
    api_products = []
    if live_res.get("success"):
        api_products = live_res.get("data", {}).get("productos", [])

    # Devolver únicamente productos reales de la cuenta Dropsheable (sin placeholders)
    if search:
        s_lower = search.lower()
        api_products = [p for p in api_products if s_lower in p.get("title", "").lower() or s_lower in p.get("sku", "").lower() or s_lower in p.get("category", "").lower()]
    if category and category != "Todos":
        api_products = [p for p in api_products if category.lower() in p.get("category", "").lower()]
    if supplier_id:
        api_products = [p for p in api_products if p.get("supplier_id") == supplier_id]

    return {
        "source": "dropsheable_live_account",
        "total": len(api_products),
        "products": api_products,
        "is_empty": len(api_products) == 0,
        "message": "Tu cuenta de Dropsheable (MinSeller #4754) está conectada con éxito. Vincula tus proveedores o productos en dropsheable.com.ar para verlos aquí."
    }

def import_product_to_store(product: dict, custom_sale_price: Optional[float] = None) -> Dict[str, Any]:
    """Imports or updates a Dropsheable product directly into the EcoMarvex store."""
    conn = get_connection()
    c = conn.cursor()

    sku = product.get("sku") or product.get("supplier_sku") or f"DSH-{product.get('id')}"
    cost_price = float(product.get("cost_price", 0.0))
    sale_price = float(custom_sale_price) if custom_sale_price is not None else float(product.get("suggested_price", cost_price * 1.5))
    
    title = product.get("title", "Producto Dropsheable").strip()
    description = product.get("description", "").strip()
    category = product.get("category", "General").strip()
    image_url = product.get("image_url", "").strip()
    stock = int(product.get("stock", 10))
    supplier_name = product.get("supplier_name", "Dropsheable Mayorista").strip()
    shipping_origin = product.get("shipping_origin", "CABA / GBA").strip()
    dispatch_time = product.get("dispatch_time", "24-48 hs hábiles").strip()
    supplier_url = f"https://dropsheable.com.ar/frontv2/producto?sku={sku}"

    # Check if product with this SKU already exists
    c.execute("SELECT id FROM products WHERE supplier_sku=?", (sku,))
    existing = c.fetchone()

    if existing:
        prod_id = existing["id"]
        c.execute("""
        UPDATE products SET
            title=?, description=?, category=?, image_url=?,
            cost_price=?, sale_price=?, stock=?, supplier_name=?,
            shipping_origin=?, dispatch_time=?, supplier_url=?, active=1
        WHERE id=?
        """, (
            title, description, category, image_url,
            cost_price, sale_price, stock, supplier_name,
            shipping_origin, dispatch_time, supplier_url, prod_id
        ))
        action = "actualizado"
    else:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO products (
            title, description, category, image_url,
            cost_price, sale_price, discount_price, stock,
            supplier_sku, supplier_url, supplier_name,
            shipping_origin, dispatch_time, featured, active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?, ?, 0, 1, ?)
        """, (
            title, description, category, image_url,
            cost_price, sale_price, stock,
            sku, supplier_url, supplier_name,
            shipping_origin, dispatch_time, created_at
        ))
        prod_id = c.lastrowid
        action = "importado"

    conn.commit()
    conn.close()

    return {
        "success": True,
        "action": action,
        "product_id": prod_id,
        "title": title,
        "sku": sku,
        "sale_price": sale_price,
        "cost_price": cost_price,
        "margin": round(sale_price - cost_price, 2)
    }

def sync_stock_with_dropsheable() -> Dict[str, Any]:
    """Syncs inventory and prices with Dropsheable live API."""
    settings = get_settings()
    api_key = settings.get("dropsheable_api_key", "").strip()
    api_secret = settings.get("dropsheable_api_secret", "").strip()

    if not api_key:
        return {"success": False, "error": "No hay API Key configurada"}

    stock_res = _make_request("/stock", api_key, api_secret)
    changes_res = _make_request("/stock/cambios?desde=2024-01-01%2000:00:00", api_key, api_secret)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, supplier_sku, stock FROM products WHERE active=1 AND supplier_sku IS NOT NULL")
    local_prods = [dict(r) for r in c.fetchall()]

    updated_count = 0
    if stock_res.get("success") and stock_res.get("data", {}).get("stock"):
        dropsheable_stock = {s.get("sku"): s.get("stock", 0) for s in stock_res["data"]["stock"]}
        for p in local_prods:
            sku = p["supplier_sku"]
            if sku in dropsheable_stock:
                new_stock = int(dropsheable_stock[sku])
                if new_stock != p["stock"]:
                    c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, p["id"]))
                    updated_count += 1
        conn.commit()

    conn.close()
    return {
        "success": True,
        "local_products_checked": len(local_prods),
        "updated_count": updated_count,
        "api_stock_items": len(stock_res.get("data", {}).get("stock", []))
    }
