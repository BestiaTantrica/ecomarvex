#!/usr/bin/env python3
"""
Publicador automático de TikTok para EcoMarvex utilizando método de cookies / sesión.
No requiere aprobación de TikTok Developer API y está 100% aislado de otras cuentas.
"""
import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

COOKIES_FILE = CREDENTIALS_DIR / "tiktok_cookies.txt"
SESSIONID_FILE = CREDENTIALS_DIR / "tiktok_sessionid.txt"

def auto_discover_cookies():
    """Busca automáticamente si el usuario descargó las cookies en su carpeta Descargas."""
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 50:
        return True
        
    descargas_dir = Path("/home/tomas2/Descargas")
    if descargas_dir.exists():
        candidates = list(descargas_dir.glob("*tiktok*.txt")) + list(descargas_dir.glob("*cookie*.txt"))
        if candidates:
            import shutil
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            shutil.copy2(newest, COOKIES_FILE)
            print(f"✅ Se detectaron y copiaron automáticamente cookies desde: {newest.name}")
            return True
    return False

def login_and_save_cookies():
    """Abre un navegador Playwright para iniciar sesión en TikTok una sola vez y guardar cookies."""
    print("=" * 65)
    print("🌐 INICIANDO NAVEGADOR PARA LOGIN DE TIKTOK (@ecomarvex)")
    print("=" * 65)
    from playwright.sync_api import sync_playwright
    from tiktok_uploader.auth import save_cookies
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")
        print("👉 Iniciá sesión en la ventana del navegador con tu cuenta de TikTok (@ecomarvex)...")
        print("💡 TIP: Podés elegir 'Iniciar sesión con código QR' y escanearlo desde la app de tu celular en 2 segundos.")
        print("👉 Una vez que veas tu feed o perfil logueado, volvé acá y presioná ENTER.")
        input("Presioná ENTER cuando hayas completado el inicio de sesión...")
        
        cookies = context.cookies()
        save_cookies(str(COOKIES_FILE), cookies)
                
        print(f"✅ ¡Cookies guardadas con éxito en {COOKIES_FILE}!")
        browser.close()

def upload_to_tiktok(video_path, description, sessionid=None):
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
    has_cookies = auto_discover_cookies()
    has_sessionid = sessionid or (SESSIONID_FILE.exists() and SESSIONID_FILE.read_text().strip())
    
    if not has_cookies and not has_sessionid:
        print("=" * 65)
        print("⚠️  FALTAN LAS COOKIES DE SESIÓN DE TIKTOK")
        print("=" * 65)
        print("Podés obtenerlas de forma muy rápida:")
        print("1. En Chrome con la extensión 'Get cookies.txt LOCALLY' en la pestaña de TikTok.")
        print("   Al descargar el archivo en Descargas, este script lo detecta automáticamente.")
        print("2. O con F12 en Chrome -> Application -> Cookies -> copiar el valor de 'sessionid'.")
        print("3. O ejecutando el login interactivo local:")
        print(f"   /home/ecomarvex/venv/bin/python3 {__file__} --login")
        print("=" * 65)
        sys.exit(1)
        
    from tiktok_uploader import upload_video
    
    print(f"🚀 Subiendo a TikTok (@ecomarvex): {Path(video_path).name}...")
    print(f"📝 Descripción: {description}")
    
    upload_kwargs = {
        "filename": str(video_path),
        "description": description,
        "headless": True,
        "browser": "chromium"
    }
    
    if has_cookies:
        upload_kwargs["cookies"] = str(COOKIES_FILE)
    elif has_sessionid:
        upload_kwargs["sessionid"] = sessionid or SESSIONID_FILE.read_text().strip()
    
    failed_videos = upload_video(**upload_kwargs)
    
    if not failed_videos:
        print("=" * 60)
        print("🎉 ¡VIDEO PUBLICADO EN TIKTOK CON ÉXITO!")
        print("=" * 60)
    else:
        print(f"❌ Error al subir a TikTok. Videos fallidos: {failed_videos}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publicador de TikTok para EcoMarvex")
    parser.add_argument("--video", type=str, default=str(BASE_DIR / "output/promo_khamrah_hook_viral_23s.mp4"), help="Ruta al video .mp4")
    parser.add_argument("--desc", type=str, default="Por favor no lo compres si odiás llamar la atención ☕✨ Perfume árabe original Lattafa Khamrah Qahwa con 10% OFF y envío gratis en ecomarvex.com 🇦🇷 #perfumesarabes #khamrahqahwa #ecomarvex #fragancias #argentina", help="Descripción del video")
    parser.add_argument("--login", action="store_true", help="Abrir navegador para iniciar sesión y guardar cookies")
    parser.add_argument("--sessionid", type=str, default=None, help="Valor directo de la cookie sessionid de TikTok")
    
    args = parser.parse_args()
    if args.login:
        login_and_save_cookies()
    else:
        upload_to_tiktok(args.video, args.desc, sessionid=args.sessionid)
