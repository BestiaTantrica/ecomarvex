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

def login_and_save_cookies():
    """Abre un navegador Playwright para iniciar sesión en TikTok una sola vez y guardar cookies."""
    print("=" * 65)
    print("🌐 INICIANDO NAVEGADOR PARA LOGIN DE TIKTOK (@ecomarvex)")
    print("=" * 65)
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")
        print("👉 Iniciá sesión en la ventana del navegador con ecomarvex@gmail.com...")
        print("👉 Una vez que veas tu feed o perfil logueado, volvé acá y presioná ENTER.")
        input("Presioná ENTER cuando hayas completado el inicio de sesión...")
        
        # Guardar cookies en formato Netscape para tiktok-uploader
        cookies = context.cookies()
        with open(COOKIES_FILE, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in cookies:
                domain = c["domain"]
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c["path"]
                secure = "TRUE" if c["secure"] else "FALSE"
                expiry = str(int(c.get("expires", 0)))
                name = c["name"]
                value = c["value"]
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
                
        print(f"✅ ¡Cookies guardadas con éxito en {COOKIES_FILE}!")
        browser.close()

def upload_to_tiktok(video_path, description):
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
    if not COOKIES_FILE.exists():
        print("=" * 65)
        print("⚠️  FALTAN LAS COOKIES DE SESIÓN DE TIKTOK")
        print("=" * 65)
        print("Podés obtenerlas de dos formas:")
        print("1. Ejecutar el login interactivo local:")
        print(f"   /home/ecomarvex/venv/bin/python3 {__file__} --login")
        print("2. O exportar las cookies desde tu navegador de PC con una extensión")
        print("   como 'Get cookies.txt LOCALLY' y pegarlas en:")
        print(f"   📁 {COOKIES_FILE}")
        print("=" * 65)
        sys.exit(1)
        
    from tiktok_uploader import upload_video
    
    print(f"🚀 Subiendo a TikTok (@ecomarvex): {Path(video_path).name}...")
    print(f"📝 Descripción: {description}")
    
    failed_videos = upload_video(
        filename=str(video_path),
        description=description,
        cookies=str(COOKIES_FILE),
        headless=True,
        browser="chromium"
    )
    
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
    
    args = parser.parse_args()
    if args.login:
        login_and_save_cookies()
    else:
        upload_to_tiktok(args.video, args.desc)
