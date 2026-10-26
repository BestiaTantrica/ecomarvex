#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = ASSETS_DIR / "fonts"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EDGE_TTS_BIN = "/home/LAB/astrology_factory/venv/bin/edge-tts"
VOICE = "es-AR-TomasNeural"
FONT_ANTON = str(FONTS_DIR / "Anton-Regular.ttf")
FONT_MONTSERRAT = str(FONTS_DIR / "Montserrat-Black.ttf")

def run_cmd(cmd, desc=""):
    print(f"🎬 {desc}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ Error en {desc}:\n{res.stderr}")
        raise Exception(f"Comando falló: {desc}")
    return res.stdout

def get_audio_duration(audio_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path)
    ]
    out = run_cmd(cmd, f"Midiendo {Path(audio_path).name}").strip()
    return float(out)

def generate_tts(text, output_mp3, rate="+5%"):
    cmd = [
        EDGE_TTS_BIN,
        "--voice", VOICE,
        "--text", text,
        "--write-media", str(output_mp3),
        f"--rate={rate}"
    ]
    run_cmd(cmd, f"Generando voz: {Path(output_mp3).name}")
    return get_audio_duration(output_mp3)

def create_fast_video():
    print("=" * 60)
    print("⚡ ECO-MARVEX — Generador de Video Rápido al Hueso (20-22s)")
    print("=" * 60)

    # 1. Assets
    product_khamrah = ASSETS_DIR / "product_khamrah.jpg"
    velador_img = Path("/home/ecomarvex/static/images/velador-rojo.png")
    banner_img = Path("/home/ecomarvex/static/images/ecomarvex_banner_1180_completo.png")
    logo_img = Path("/home/ecomarvex/logo/ecomarvex_logo_500x500.png")

    # 2. Textos de locución optimizados (fonética cuidada: "Éco Márvex" para dicción perfecta)
    # Parte 1: Gancho veloz (0s - ~4.5s)
    t1 = "Si buscás perfumes árabes originales y productos virales en Argentina, tenés que conocer Éco Márvex."
    # Parte 2: Confianza y Mercado Pago (4.5s - ~13s)
    t2 = "Comprás cien por ciento seguro con Mercado Pago, o aprovechás diez por ciento de descuento extra pagando por transferencia directa."
    # Parte 3: Despacho y CTA final (13s - ~21s)
    t3 = "Hacemos envíos rápidos a todo el país. Conseguí el tuyo en ecomarvex.com entrando al link de nuestro perfil."

    a1 = ASSETS_DIR / "fast_part1.mp3"
    a2 = ASSETS_DIR / "fast_part2.mp3"
    a3 = ASSETS_DIR / "fast_part3.mp3"

    dur1 = generate_tts(t1, a1, rate="+7%")
    dur2 = generate_tts(t2, a2, rate="+7%")
    dur3 = generate_tts(t3, a3, rate="+7%")
    total_dur = dur1 + dur2 + dur3

    print(f"⏱️ Duraciones: Parte 1: {dur1:.2f}s | Parte 2: {dur2:.2f}s | Parte 3: {dur3:.2f}s | Total: {total_dur:.2f}s")

    # Unir audios
    concat_list = ASSETS_DIR / "fast_audio_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{a1}'\n")
        f.write(f"file '{a2}'\n")
        f.write(f"file '{a3}'\n")

    master_audio = ASSETS_DIR / "fast_master_audio.mp3"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(master_audio)
    ], "Uniendo audio master")

    # 3. Clip 1: Gancho con Producto Estrella (Khamrah) y Tipografía Anton / Montserrat
    clip1 = ASSETS_DIR / "fast_clip1.mp4"
    vf1 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0012,1.18)':d={int(dur1*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=80:color=black@0.80:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='PERFUMES ARABES Y VIRALES':fontcolor=#FDE047:fontsize=64:x=(w-text_w)/2:y=110,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='STOCK REAL EN ARGENTINA':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=200,"
        f"drawbox=y=ih-320:color=black@0.85:width=iw:height=200:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='DESCUBRI ECO MARVEX':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=h-280,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='TIENDA OFICIAL ONLINE':fontcolor=#38BDF8:fontsize=34:x=(w-text_w)/2:y=h-190"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(product_khamrah),
        "-vf", vf1, "-t", f"{dur1:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip1)
    ], "Renderizando Clip 1 (Gancho Producto)")

    # 4. Clip 2: Confianza y Mercado Pago (Velador / Tienda)
    clip2 = ASSETS_DIR / "fast_clip2.mp4"
    vf2 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0010,1.15)':d={int(dur2*30)}:s=1080x1920:fps=30,"
        # Bloque Mercado Pago Oficial
        f"drawbox=y=100:color=0x009EE3@0.95:width=iw:height=240:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='PAGOS 100% PROTEGIDOS':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=135,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='COMPRA SEGURA CON MERCADO PAGO':fontcolor=#FEF08A:fontsize=36:x=(w-text_w)/2:y=220,"
        # Bloque Descuento Transferencia
        f"drawbox=y=ih-420:color=black@0.88:width=iw:height=280:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='10% DE DESCUENTO EXTRA':fontcolor=#4ADE80:fontsize=58:x=(w-text_w)/2:y=h-380,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='PAGANDO POR TRANSFERENCIA DIRECTA':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=h-290,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='O EN CUOTAS CON TU TARJETA':fontcolor=#94A3B8:fontsize=32:x=(w-text_w)/2:y=h-220"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(velador_img),
        "-vf", vf2, "-t", f"{dur2:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip2)
    ], "Renderizando Clip 2 (Mercado Pago y Confianza)")

    # 5. Clip 3: Envíos y Cierre Web (Banner / Logo)
    clip3 = ASSETS_DIR / "fast_clip3.mp4"
    vf3 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.08)':d={int(dur3*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=0:color=black@0.90:width=iw:height=ih:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='ENVIOS A TODO EL PAIS':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=340,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='POR ANDREANI Y CORREO ARGENTINO':fontcolor=#38BDF8:fontsize=36:x=(w-text_w)/2:y=430,"
        f"drawtext=fontfile='{FONT_ANTON}':text='DESPACHO EN 24 A 48 HORAS':fontcolor=#FDE047:fontsize=48:x=(w-text_w)/2:y=520,"
        # Llamado a la acción central
        f"drawbox=y=ih-600:color=#1E1B4B@0.95:width=iw:height=360:t=fill,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='COMPRA DIRECTO EN NUESTRA WEB':fontcolor=#A5B4FC:fontsize=34:x=(w-text_w)/2:y=h-540,"
        f"drawtext=fontfile='{FONT_ANTON}':text='ecomarvex.com':fontcolor=white:fontsize=84:x=(w-text_w)/2:y=h-460,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='TOCA EL ENLACE DE NUESTRO PERFIL':fontcolor=#FDE047:fontsize=36:x=(w-text_w)/2:y=h-330"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(product_khamrah),
        "-vf", vf3, "-t", f"{dur3:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip3)
    ], "Renderizando Clip 3 (Envíos y CTA Final)")

    # 6. Unir los 3 clips
    video_list = ASSETS_DIR / "fast_video_list.txt"
    with open(video_list, "w") as f:
        f.write(f"file '{clip1}'\n")
        f.write(f"file '{clip2}'\n")
        f.write(f"file '{clip3}'\n")

    video_concat = ASSETS_DIR / "fast_video_concat.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list), "-c", "copy", str(video_concat)
    ], "Uniendo clips rápidos")

    # 7. Audio + Video Master
    final_output = OUTPUT_DIR / "promo_ecomarvex_rapido_22s.mp4"
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(video_concat),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output)
    ], "Ensamblando Video Final Rápido")

    print("=" * 60)
    print(f"🎉 ¡VIDEO RÁPIDO GENERADO!")
    print(f"📁 Ubicación: {final_output}")
    size_mb = final_output.stat().st_size / (1024 * 1024)
    print(f"📊 Peso: {size_mb:.2f} MB | Duración: {total_dur:.1f} segundos")
    print("=" * 60)
    return str(final_output)

if __name__ == "__main__":
    create_fast_video()
