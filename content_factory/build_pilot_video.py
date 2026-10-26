#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EDGE_TTS_BIN = "/home/LAB/astrology_factory/venv/bin/edge-tts"
VOICE = "es-AR-ElenaNeural"
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

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
    out = run_cmd(cmd, f"Obteniendo duración de {Path(audio_path).name}").strip()
    return float(out)

def generate_tts_clip(text, output_mp3, rate="+0%"):
    cmd = [
        EDGE_TTS_BIN,
        "--voice", VOICE,
        "--text", text,
        "--write-media", str(output_mp3),
        f"--rate={rate}"
    ]
    run_cmd(cmd, f"Generando audio TTS: {Path(output_mp3).name}")
    return get_audio_duration(output_mp3)

def create_video():
    print("=" * 60)
    print("🚀 ECO-MARVEX CONTENT FACTORY — Generador de Video Piloto 9:16")
    print("=" * 60)

    # 1. Rutas de Assets
    avatar_img = ASSETS_DIR / "avatar_hook.jpg"
    product_img = ASSETS_DIR / "product_khamrah.jpg"
    logo_img = Path("/home/ecomarvex/logo/ecomarvex_logo_500x500.png")

    if not avatar_img.exists():
        raise Exception(f"No se encontró el avatar: {avatar_img}")
    if not product_img.exists():
        raise Exception(f"No se encontró el producto: {product_img}")
    if not logo_img.exists():
        logo_img = Path("/home/ecomarvex/static/images/ecomarvex_logo_500x500.png")

    # 2. Generar Locuciones
    audio_part1 = ASSETS_DIR / "audio_part1.mp3"
    audio_part2 = ASSETS_DIR / "audio_part2.mp3"
    audio_part3 = ASSETS_DIR / "audio_part3.mp3"

    text1 = "¡Pará un segundo! ¿Por qué todo el mundo en TikTok está obsesionado con este perfume árabe y nadie quiere volver a los tradicionales? Mirá esto."
    text2 = "Te presento el Lattafa Khamrah Qahwa. Una bomba con notas de café tostado, canela, praliné y vainilla ahumada. Tiene una fijación de más de doce horas en piel y una estela que se siente a metros de distancia. Lujo oriental auténtico."
    text3 = "Aprovechá la promoción con envío gratis a todo el país y diez por ciento de descuento extra pagando por transferencia directa. Pedí el tuyo en ecomarvex.com antes de que se agote el stock."

    dur1 = generate_tts_clip(text1, audio_part1, rate="+3%")
    dur2 = generate_tts_clip(text2, audio_part2, rate="+3%")
    dur3 = generate_tts_clip(text3, audio_part3, rate="+3%")

    print(f"⏱️ Duraciones: Parte 1: {dur1:.2f}s | Parte 2: {dur2:.2f}s | Parte 3: {dur3:.2f}s | Total: {dur1+dur2+dur3:.2f}s")

    # Unir audios
    concat_list = ASSETS_DIR / "audio_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{audio_part1}'\n")
        f.write(f"file '{audio_part2}'\n")
        f.write(f"file '{audio_part3}'\n")

    master_audio = ASSETS_DIR / "master_audio.mp3"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(master_audio)
    ], "Concatenando audio master")

    # 3. Generar Clip 1: Avatar Gancho (0s a dur1)
    clip1 = ASSETS_DIR / "clip1.mp4"
    vf1 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.08)':d={int(dur1*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=ih-380:color=black@0.65:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_PATH}':text='¿POR QUÉ TODO TIKTOK':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-350,"
        f"drawtext=fontfile='{FONT_PATH}':text='HABLA DE ESTE PERFUME?':fontcolor=#FBBF24:fontsize=54:x=(w-text_w)/2:y=h-280"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(avatar_img),
        "-vf", vf1, "-t", f"{dur1:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip1)
    ], "Renderizando Clip 1 (Gancho Avatar)")

    # 4. Generar Clip 2: Vitrina Dinámica del Producto (dur1 a dur1+dur2)
    clip2 = ASSETS_DIR / "clip2.mp4"
    vf2 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0008,1.15)':d={int(dur2*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=60:color=black@0.75:width=iw:height=180:t=fill,"
        f"drawtext=fontfile='{FONT_PATH}':text='LATTAFA KHAMRAH QAHWA':fontcolor=#FDE047:fontsize=52:x=(w-text_w)/2:y=100,"
        f"drawtext=fontfile='{FONT_PATH}':text='100% ORIGINAL • EDICION ARABE':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=165,"
        f"drawbox=y=ih-420:color=black@0.75:width=iw:height=280:t=fill,"
        f"drawtext=fontfile='{FONT_PATH}':text='NOTAS DE CAFE TOSTADO Y PRALINE':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=h-380,"
        f"drawtext=fontfile='{FONT_PATH}':text='MAS DE 12 HORAS DE FIJACION':fontcolor=#38BDF8:fontsize=38:x=(w-text_w)/2:y=h-310,"
        f"drawtext=fontfile='{FONT_PATH}':text='ESTELA POTENTE Y ADICTIVA':fontcolor=#FBBF24:fontsize=38:x=(w-text_w)/2:y=h-240"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(product_img),
        "-vf", vf2, "-t", f"{dur2:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip2)
    ], "Renderizando Clip 2 (Vitrina Producto)")

    # 5. Generar Clip 3: Cierre y Oferta EcoMarvex (dur3)
    clip3 = ASSETS_DIR / "clip3.mp4"
    vf3 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0005,1.06)':d={int(dur3*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=0:color=black@0.85:width=iw:height=ih:t=fill,"
        f"drawtext=fontfile='{FONT_PATH}':text='OFERTA EXCLUSIVA':fontcolor=#FBBF24:fontsize=62:x=(w-text_w)/2:y=300,"
        f"drawtext=fontfile='{FONT_PATH}':text='ENVIO GRATIS A TODO EL PAIS':fontcolor=white:fontsize=44:x=(w-text_w)/2:y=450,"
        f"drawtext=fontfile='{FONT_PATH}':text='10% OFF EXTRA POR TRANSFERENCIA':fontcolor=#4ADE80:fontsize=44:x=(w-text_w)/2:y=540,"
        f"drawtext=fontfile='{FONT_PATH}':text='DESPACHO EN 24-48 HORAS':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=630,"
        f"drawbox=y=ih-520:color=black@0.9:width=iw:height=320:t=fill,"
        f"drawtext=fontfile='{FONT_PATH}':text='COMPRA ONLINE EN':fontcolor=#A5B4FC:fontsize=38:x=(w-text_w)/2:y=h-480,"
        f"drawtext=fontfile='{FONT_PATH}':text='ecomarvex.com':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=h-400,"
        f"drawtext=fontfile='{FONT_PATH}':text='TOCA EL ENLACE EN NUESTRO PERFIL':fontcolor=#FDE047:fontsize=36:x=(w-text_w)/2:y=h-290"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(product_img),
        "-vf", vf3, "-t", f"{dur3:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip3)
    ], "Renderizando Clip 3 (Cierre Comercial)")

    # 6. Concatenar los 3 clips de video
    video_list = ASSETS_DIR / "video_list.txt"
    with open(video_list, "w") as f:
        f.write(f"file '{clip1}'\n")
        f.write(f"file '{clip2}'\n")
        f.write(f"file '{clip3}'\n")

    video_concat = ASSETS_DIR / "video_concat.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list), "-c", "copy", str(video_concat)
    ], "Uniendo clips de video")

    # 7. Unir Video y Audio Master Final
    final_output = OUTPUT_DIR / "promo_lattafa_khamrah.mp4"
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(video_concat),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output)
    ], "Ensamblando Video Final con Audio Master")

    print("=" * 60)
    print(f"🎉 ¡VIDEO GENERADO CON ÉXITO!")
    print(f"📁 Ubicación: {final_output}")
    size_mb = final_output.stat().st_size / (1024 * 1024)
    print(f"📊 Peso: {size_mb:.2f} MB")
    print("=" * 60)
    return str(final_output)

if __name__ == "__main__":
    create_video()
