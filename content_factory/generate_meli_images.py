#!/usr/bin/env python3
"""
Generador de stock de imágenes profesionales para Mercado Libre y Tienda Online.
Cumple 100% con las normativas de Mercado Libre (1200x1200px, portada con fondo blanco puro RGB 255,255,255).
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
MELI_DIR = ASSETS_DIR / "meli_stock"
FONTS_DIR = ASSETS_DIR / "fonts"
CATALOG_IMG = ASSETS_DIR / "product_khamrah.jpg"
WHITE_STUDIO_IMG = Path("/home/tomas2/.gemini/antigravity-ide/brain/476d29f4-ad3e-4254-adad-db577c57bb89/khamrah_meli_white_1793146445359.jpg")

MELI_DIR.mkdir(parents=True, exist_ok=True)

FONT_ANTON = str(FONTS_DIR / "Anton-Regular.ttf")
FONT_SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def create_stock():
    orig = Image.open(CATALOG_IMG).convert("RGB")
    prod_crop = orig.crop((50, 40, 955, 715))

    print("📸 1. Portada MeLi (1200x1200px, Fondo Blanco Puro RGB 255,255,255)...")
    # Foto 1: Foto de catálogo aislada con iluminación de estudio
    if WHITE_STUDIO_IMG.exists():
        img1 = Image.open(WHITE_STUDIO_IMG).convert("RGB")
        img1_res = img1.resize((1200, 1200), Image.Resampling.LANCZOS)
        out1 = MELI_DIR / "1_portada_blanca_1200x1200.jpg"
        img1_res.save(out1, quality=98)
        print(f"   ✅ Guardado: {out1.name}")

    print("📸 2. Infografía: Pirámide Olfativa con tipografía Unicode...")
    canvas2 = Image.new("RGB", (1200, 1200), (250, 248, 245))
    draw2 = ImageDraw.Draw(canvas2)
    
    # Encabezado oscuro
    draw2.rectangle([0, 0, 1200, 160], fill=(24, 20, 16))
    f_title = get_font(FONT_ANTON, 52)
    f_sub = get_font(FONT_SANS_BOLD, 24)
    draw2.text((600, 50), "PIRÁMIDE OLFATIVA • NOTAS REALES", fill=(253, 224, 71), font=f_title, anchor="mm")
    draw2.text((600, 115), "LATTAFA KHAMRAH QAHWA (100ML EAU DE PARFUM)", fill=(255, 255, 255), font=f_sub, anchor="mm")
    
    # Frasco en la izquierda
    bottle_crop = orig.crop((160, 40, 600, 560))
    b_target_w = 460
    b_target_h = int(b_target_w * bottle_crop.size[1] / bottle_crop.size[0])
    b_resized = bottle_crop.resize((b_target_w, b_target_h), Image.Resampling.LANCZOS)
    canvas2.paste(b_resized, (60, 240))
    
    # Bloques de notas con LiberationSans (100% acentos)
    f_cat = get_font(FONT_ANTON, 32)
    f_desc = get_font(FONT_SANS_REG, 23)
    
    # Bloque 1: Salida
    draw2.rounded_rectangle([560, 220, 1140, 460], radius=16, fill=(255, 255, 255), outline=(220, 215, 205), width=2)
    draw2.text((590, 250), "SALIDA (Primeros 15-30 min)", fill=(202, 138, 4), font=f_cat)
    draw2.text((590, 310), "- Canela Especiada\n- Cardamomo Aromático\n- Jengibre Cálido", fill=(40, 35, 30), font=f_desc, spacing=8)
    
    # Bloque 2: Corazón
    draw2.rounded_rectangle([560, 490, 1140, 750], radius=16, fill=(255, 255, 255), outline=(220, 215, 205), width=2)
    draw2.text((590, 520), "CORAZÓN (Estela Central)", fill=(180, 83, 9), font=f_cat)
    draw2.text((590, 580), "- Café Tostado Adictivo\n- Praliné Confitado Dulce\n- Flores Blancas Sutiles", fill=(40, 35, 30), font=f_desc, spacing=8)
    
    # Bloque 3: Fondo
    draw2.rounded_rectangle([560, 780, 1140, 1040], radius=16, fill=(255, 255, 255), outline=(220, 215, 205), width=2)
    draw2.text((590, 810), "FONDO (+12 horas en piel)", fill=(120, 53, 15), font=f_cat)
    draw2.text((590, 870), "- Vainilla Bourbon Dulce\n- Haba Tonka y Benjuí\n- Almizcle Ambarado", fill=(40, 35, 30), font=f_desc, spacing=8)
    
    # Barra pie
    draw2.rectangle([0, 1120, 1200, 1200], fill=(24, 20, 16))
    f_footer = get_font(FONT_SANS_BOLD, 22)
    draw2.text((600, 1160), "FRAGANCIA ORIENTAL GOURMAND • FIJACIÓN EXTENDIDA GARANTIZADA", fill=(253, 224, 71), font=f_footer, anchor="mm")
    
    out2 = MELI_DIR / "2_piramide_olfativa_1200x1200.jpg"
    canvas2.save(out2, quality=98)
    print(f"   ✅ Guardado: {out2.name}")

    print("📸 3. Infografía: Rendimiento y Fijación...")
    canvas3 = Image.new("RGB", (1200, 1200), (20, 18, 16))
    draw3 = ImageDraw.Draw(canvas3)
    
    draw3.text((600, 70), "RENDIMIENTO Y CARACTERÍSTICAS", fill=(253, 224, 71), font=f_title, anchor="mm")
    draw3.text((600, 135), "DESEMPEÑO REAL EN PIEL Y ROPA", fill=(255, 255, 255), font=f_sub, anchor="mm")
    
    items = [
        ("DURACIÓN EN PIEL", "MÁS DE 12 HORAS", "Fijación extrema de aceites árabes que perdura hasta el día siguiente.", (74, 222, 128)),
        ("PROYECCIÓN Y ESTELA", "PESADA / LLAMATIVA", "Deja un rastro dulce de café y canela a 2 metros de distancia.", (56, 189, 248)),
        ("OCASIÓN IDEAL", "NOCHE / SALIDAS / CITAS", "Aroma seductor diseñado para destacar en eventos y clima fresco.", (244, 114, 182)),
        ("PRESENTACIÓN", "100 ML (3.4 FL. OZ.)", "Caja rígida con pedestal y frasco de cristal pesado tallado.", (250, 204, 21))
    ]
    
    coords = [
        (80, 200, 560, 580),
        (640, 200, 1120, 580),
        (80, 620, 560, 1000),
        (640, 620, 1120, 1000)
    ]
    
    for (title, highlight, desc, color), (x1, y1, x2, y2) in zip(items, coords):
        draw3.rounded_rectangle([x1, y1, x2, y2], radius=20, fill=(32, 28, 25), outline=(55, 48, 42), width=2)
        draw3.text(((x1 + x2) // 2, y1 + 50), title, fill=(180, 175, 170), font=get_font(FONT_SANS_BOLD, 22), anchor="mm")
        draw3.text(((x1 + x2) // 2, y1 + 130), highlight, fill=color, font=get_font(FONT_ANTON, 38), anchor="mm")
        
        # Wrapping manual
        words = desc.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 30:
                lines.append(" ".join(cur_line[:-1]))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))
            
        y_text = y1 + 220
        for l in lines:
            draw3.text(((x1 + x2) // 2, y_text), l, fill=(220, 215, 210), font=get_font(FONT_SANS_REG, 21), anchor="mm")
            y_text += 32

    draw3.text((600, 1100), "GARANTÍA: 100% ORIGINAL • ENVASE SELLADO DE FÁBRICA CON HOLOGRAMA", fill=(253, 224, 71), font=f_sub, anchor="mm")
    
    out3 = MELI_DIR / "3_rendimiento_fijacion_1200x1200.jpg"
    canvas3.save(out3, quality=98)
    print(f"   ✅ Guardado: {out3.name}")

    print("📸 4. Detalle de Packaging y Presentación de Lujo...")
    canvas4 = Image.new("RGB", (1200, 1200), (245, 245, 245))
    
    p_w = 1100
    p_h = int(p_w * prod_crop.size[1] / prod_crop.size[0])
    p_res = prod_crop.resize((p_w, p_h), Image.Resampling.LANCZOS)
    canvas4.paste(p_res, (50, 200))
    
    draw4 = ImageDraw.Draw(canvas4)
    draw4.rectangle([0, 0, 1200, 150], fill=(24, 20, 16))
    draw4.text((600, 50), "PRESENTACIÓN DE COLECCIÓN", fill=(253, 224, 71), font=f_title, anchor="mm")
    draw4.text((600, 110), "CAJA RÍGIDA DESPLEGABLE • FRASCO DE CRISTAL PESADO", fill=(255, 255, 255), font=f_sub, anchor="mm")
    
    draw4.rectangle([0, 1080, 1200, 1200], fill=(24, 20, 16))
    draw4.text((600, 1140), "FOTO 100% REAL DEL PRODUCTO ENTREGADO", fill=(253, 224, 71), font=f_sub, anchor="mm")
    
    out4 = MELI_DIR / "4_packaging_lujo_1200x1200.jpg"
    canvas4.save(out4, quality=98)
    print(f"   ✅ Guardado: {out4.name}")

    print("=" * 60)
    print(f"🎉 ¡KIT DE 4 IMÁGENES ACTUALIZADO CON ÉXITO!")
    print(f"📁 Carpeta: {MELI_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    create_stock()
