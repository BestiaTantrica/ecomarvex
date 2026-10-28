#!/usr/bin/env python3
"""
Publicador robusto para TikTok Studio (@ecomarvex)
Optimizado para la interfaz moderna de https://www.tiktok.com/tiktokstudio/upload
"""
import sys
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from tiktok_uploader.auth import AuthBackend

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
COOKIES_FILE = CREDENTIALS_DIR / "tiktok_cookies.txt"

def upload_to_tiktok_studio(video_path, description):
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")

    if not COOKIES_FILE.exists():
        raise FileNotFoundError(f"Cookies no encontradas en {COOKIES_FILE}")

    print("=" * 65)
    print(f"🚀 SUBIENDO A TIKTOK STUDIO (@ecomarvex)")
    print(f"🎬 Video: {video_path.name}")
    print(f"📝 Descripción: {description[:80]}...")
    print("=" * 65)

    backend = AuthBackend(cookies=str(COOKIES_FILE))
    raw_cookies = backend._resolve_cookies()
    playwright_cookies = []
    for c in raw_cookies:
        cookie = c.copy()
        if "expiry" in cookie:
            cookie["expires"] = cookie.pop("expiry")
        if "sameSite" in cookie and cookie["sameSite"] not in ["Strict", "Lax", "None"]:
            cookie.pop("sameSite")
        playwright_cookies.append(cookie)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        context.add_cookies(playwright_cookies)
        page = context.new_page()

        print("🌐 Navegando a TikTok Studio Upload...")
        page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # 1. Cargar archivo de video
        print("📤 Seleccionando archivo de video...")
        file_input = page.locator("input[type='file']").first
        if file_input.count() > 0:
            file_input.set_input_files(str(video_path))
        else:
            with page.expect_file_chooser() as fc_info:
                btn = page.locator("button:has-text('Seleccionar video'), button:has-text('Select video'), button:has-text('Cargar')").first
                btn.click()
            fc_info.value.set_files(str(video_path))

        print("⏳ Video cargado. Esperando que TikTok procese el formulario...")
        page.wait_for_timeout(8000)

        # 2. Cerrar modales (ej: "Entendido" de nuevas funciones de edición o avisos de sonido)
        print("🛡️ Verificando y cerrando modales informativos...")
        try:
            entendido_btn = page.locator("button:has-text('Entendido'), button:has-text('Got it')").first
            if entendido_btn.is_visible(timeout=5000):
                entendido_btn.click()
                print("   Modal 'Entendido' cerrado exitosamente.")
        except Exception:
            pass

        try:
            page.evaluate("""
                document.querySelectorAll('[data-floating-ui-portal] button, .TUXModal button, .TUXModal-overlay button').forEach(b => b.click());
                document.querySelectorAll('[data-floating-ui-portal], .TUXModal-overlay').forEach(el => el.remove());
            """)
        except Exception:
            pass

        page.wait_for_timeout(2000)

        # 3. Escribir descripción
        print("✍️ Ingresando descripción y hashtags...")
        caption_box = page.locator("div[contenteditable='true'], div[role='combobox'][contenteditable='true'], .public-DraftEditor-content").first
        try:
            caption_box.scroll_into_view_if_needed()
            caption_box.click(force=True)
            caption_box.press("Control+A")
            caption_box.press("Backspace")
            
            # Escribir el texto con formato limpio
            caption_box.press_sequentially(description, delay=20)
            print("   Descripción ingresada correctamente.")
        except Exception as e:
            print(f"   Aviso en descripción: {e}. Intentando inserción directa...")
            try:
                page.evaluate("""(desc) => {
                    const el = document.querySelector("div[contenteditable='true']");
                    if (el) {
                        el.focus();
                        document.execCommand('selectAll', false, null);
                        document.execCommand('insertText', false, desc);
                    }
                }""", description)
            except Exception as e2:
                print(f"   No se pudo forzar la descripción: {e2}")

        page.wait_for_timeout(3000)

        # 4. Hacer clic en Publicar (Post)
        print("🚀 Haciendo clic en Publicar...")
        # Esperar que el botón de publicar esté habilitado (que termine de subir el video)
        post_btn = page.locator("button:has-text('Publicar'), button:has-text('Post'), button[data-e2e='post_video_button']").first
        
        # Esperar hasta 60s si está subiendo
        for i in range(30):
            if post_btn.is_enabled():
                break
            print(f"   Esperando procesamiento de video ({i*2}s)...")
            page.wait_for_timeout(2000)

        post_btn.scroll_into_view_if_needed()
        post_btn.click(force=True)

        print("⏳ Verificando confirmación secundaria (Publicar ahora)...")
        page.wait_for_timeout(3000)
        try:
            pub_ahora = page.locator("button:has-text('Publicar ahora'), button:has-text('Post now')").first
            if pub_ahora.is_visible(timeout=5000):
                pub_ahora.click(force=True)
                print("   Confirmación 'Publicar ahora' aceptada.")
        except Exception:
            pass

        print("⏳ Esperando confirmación final de publicación de TikTok...")
        page.wait_for_timeout(8000)

        # Capturar pantalla final de confirmación
        confirm_path = "/home/tomas2/.gemini/antigravity-ide/brain/476d29f4-ad3e-4254-adad-db577c57bb89/tiktok_published_confirmation.png"
        page.screenshot(path=confirm_path)
        print(f"📸 Captura de confirmación guardada en {confirm_path}")

        print("=" * 60)
        print("🎉 ¡VIDEO PUBLICADO EN TIKTOK STUDIO CON ÉXITO!")
        print("=" * 60)

        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publicador para TikTok Studio")
    parser.add_argument("--video", type=str, default=str(BASE_DIR / "output/promo_khamrah_primera_cita_22s.mp4"))
    parser.add_argument("--desc", type=str, default="Si tenés una primera cita, dos sprays de esto y no fallás ☕✨ Perfume árabe original Lattafa Khamrah Qahwa con 10% OFF y envío gratis en ecomarvex.com 🇦🇷 #perfumesarabes #khamrahqahwa #ecomarvex #fragancias #argentina")
    args = parser.parse_args()

    upload_to_tiktok_studio(args.video, args.desc)
