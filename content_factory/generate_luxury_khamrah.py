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

def generate_tts(text, output_mp3, rate="+8%"):
    cmd = [
        EDGE_TTS_BIN,
        "--voice", VOICE,
        "--text", text,
        "--write-media", str(output_mp3),
        f"--rate={rate}"
    ]
    run_cmd(cmd, f"Generando voz: {Path(output_mp3).name}")
    return get_audio_duration(output_mp3)

def create_luxury_video():
    print("=" * 60)
    print("💎 ECO-MARVEX — Khamrah Qahwa Luxury 9:16 (23s)")
    print("=" * 60)

    # 1. Rutas de fotos reales en 9:16 nativo (1080x1920)
    shot1_pedestal = ASSETS_DIR / "shot1_pedestal.jpg"
    shot2_unboxing = ASSETS_DIR / "shot2_unboxing.jpg"
    shot3_spray = ASSETS_DIR / "shot3_spray.jpg"

    for p in [shot1_pedestal, shot2_unboxing, shot3_spray]:
        if not p.exists():
            raise Exception(f"Falta imagen: {p}")

    # 2. Textos optimizados con dicción natural ("Éco Márvex")
    t1 = "¿Buscás un perfume árabe original con fijación brutal en piel? Tenés que conocer el Lattafa Khamrah Qahwa."
    t2 = "Presentación de lujo, aroma adictivo a café tostado, praliné y canela, con más de doce horas de duración garantizada."
    t3 = "Comprás cien por ciento protegido con Mercado Pago, o con diez por ciento de descuento extra por transferencia. Pedilo con envío gratis en Éco Márvex punto com."

    a1 = ASSETS_DIR / "lux_part1.mp3"
    a2 = ASSETS_DIR / "lux_part2.mp3"
    a3 = ASSETS_DIR / "lux_part3.mp3"

    dur1 = generate_tts(t1, a1, rate="+8%")
    dur2 = generate_tts(t2, a2, rate="+8%")
    dur3 = generate_tts(t3, a3, rate="+8%")
    total_dur = dur1 + dur2 + dur3

    print(f"⏱️ Duraciones: Parte 1: {dur1:.2f}s | Parte 2: {dur2:.2f}s | Parte 3: {dur3:.2f}s | Total: {total_dur:.2f}s")

    # Unir audios
    concat_list = ASSETS_DIR / "lux_audio_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{a1}'\n")
        f.write(f"file '{a2}'\n")
        f.write(f"file '{a3}'\n")

    master_audio = ASSETS_DIR / "lux_master_audio.mp3"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(master_audio)
    ], "Uniendo audio master")

    # 3. Clip 1: Pedestal & Gancho (shot1_pedestal.jpg)
    clip1 = ASSETS_DIR / "lux_clip1.mp4"
    vf1 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.07)':d={int(dur1*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=90:color=black@0.75:width=iw:height=210:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='PERFUME ARABE ORIGINAL':fontcolor=#FDE047:fontsize=62:x=(w-text_w)/2:y=120,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='LATTAFA KHAMRAH QAHWA':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=210,"
        f"drawbox=y=ih-340:color=black@0.80:width=iw:height=200:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='FIJACION BRUTAL EN PIEL':fontcolor=#38BDF8:fontsize=52:x=(w-text_w)/2:y=h-300,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='NOTAS DE CAFE Y CANELA':fontcolor=#FEF08A:fontsize=36:x=(w-text_w)/2:y=h-210"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot1_pedestal),
        "-vf", vf1, "-t", f"{dur1:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip1)
    ], "Renderizando Clip 1 (Pedestal & Gancho)")

    # 4. Clip 2: Unboxing de Lujo (shot2_unboxing.jpg)
    clip2 = ASSETS_DIR / "lux_clip2.mp4"
    vf2 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.07)':d={int(dur2*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=90:color=black@0.75:width=iw:height=210:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='PRESENTACION DE LUJO':fontcolor=#FDE047:fontsize=62:x=(w-text_w)/2:y=120,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='CAJA RIGIDA CON DETALLES DORADOS':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=210,"
        f"drawbox=y=ih-340:color=black@0.80:width=iw:height=200:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='DURA MAS DE 12 HORAS':fontcolor=#4ADE80:fontsize=54:x=(w-text_w)/2:y=h-300,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='PRALINE, VAINILLA Y CAFE TOSTADO':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=h-210"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot2_unboxing),
        "-vf", vf2, "-t", f"{dur2:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip2)
    ], "Renderizando Clip 2 (Unboxing & Estela)")

    # 5. Clip 3: Spray en Acción + Mercado Pago + Envío Gratis (shot3_spray.jpg)
    clip3 = ASSETS_DIR / "lux_clip3.mp4"
    vf3 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0005,1.06)':d={int(dur3*30)}:s=1080x1920:fps=30,"
        # Cartel Azul Mercado Pago
        f"drawbox=y=110:color=0x009EE3@0.95:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='PAGOS SEGUROS CON MERCADO PAGO':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=140,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='COMPRA 100% PROTEGIDA':fontcolor=#FEF08A:fontsize=36:x=(w-text_w)/2:y=230,"
        # Cartel Descuento Transferencia
        f"drawbox=y=370:color=black@0.85:width=iw:height=140:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':text='10% OFF EXTRA POR TRANSFERENCIA':fontcolor=#4ADE80:fontsize=48:x=(w-text_w)/2:y=415,"
        # Bloque CTA Cierre
        f"drawbox=y=ih-480:color=0x1E1B4B@0.95:width=iw:height=360:t=fill,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='ENVIO GRATIS A TODO EL PAIS':fontcolor=#FDE047:fontsize=36:x=(w-text_w)/2:y=h-430,"
        f"drawtext=fontfile='{FONT_ANTON}':text='ecomarvex.com':fontcolor=white:fontsize=84:x=(w-text_w)/2:y=h-350,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':text='TOCA EL ENLACE EN NUESTRO PERFIL':fontcolor=#38BDF8:fontsize=34:x=(w-text_w)/2:y=h-220"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot3_spray),
        "-vf", vf3, "-t", f"{dur3:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip3)
    ], "Renderizando Clip 3 (Spray & Cierre)")

    # 6. Unir los 3 clips
    video_list = ASSETS_DIR / "lux_video_list.txt"
    with open(video_list, "w") as f:
        f.write(f"file '{clip1}'\n")
        f.write(f"file '{clip2}'\n")
        f.write(f"file '{clip3}'\n")

    video_concat = ASSETS_DIR / "lux_video_concat.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list), "-c", "copy", str(video_concat)
    ], "Uniendo clips 9:16")

    # 7. Audio + Video Master
    final_output = OUTPUT_DIR / "promo_khamrah_qahwa_23s.mp4"
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(video_concat),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output)
    ], "Ensamblando Video Final Luxury")

    print("=" * 60)
    print(f"🎉 ¡VIDEO LUXURY 9:16 GENERADO CON ÉXITO!")
    print(f"📁 Ubicación: {final_output}")
    size_mb = final_output.stat().st_size / (1024 * 1024)
    print(f"📊 Peso: {size_mb:.2f} MB | Duración: {total_dur:.1f} segundos")
    print("=" * 60)
    return str(final_output)

if __name__ == "__main__":
    create_luxury_video()
