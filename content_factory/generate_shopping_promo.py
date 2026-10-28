#!/usr/bin/env python3
"""
Generador de Video Promocional — Gancho 2: Shopping vs. Árabes (Ahorro Inteligente & Picardía)
Estructura:
1. Hook (0-4s): "¿A vos te parece normal pagar 400 mil pesos por un perfume importado que a las 3 horas desaparece?"
2. Desarrollo (4-15s): "Los árabes sacaron este bicho con notas de café y canela que dura más de doce horas y la caja parece un lingote de oro."
3. Cierre (15-23s): "Pedilo con envío gratis en Éco Márvex punto com con Mercado Pago. Si buscabas halagos, acá tenés."
"""
import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

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
CATALOG_IMG = ASSETS_DIR / "product_khamrah.jpg"

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

def generate_tts(text, output_mp3, rate="+6%"):
    cmd = [
        EDGE_TTS_BIN,
        "--voice", VOICE,
        "--text", text,
        "--write-media", str(output_mp3),
        f"--rate={rate}"
    ]
    run_cmd(cmd, f"Generando voz: {Path(output_mp3).name}")
    return get_audio_duration(output_mp3)

def prepare_frames():
    img = Image.open(CATALOG_IMG).convert("RGB")
    w, h = img.size

    def make_canvas(crop_box, fg_scale=1.0, y_offset=-40):
        canvas = Image.new("RGB", (1080, 1920), (12, 10, 8))
        bg = img.resize((1080, int(1080 * h / w)))
        if bg.size[1] < 1920:
            bg = img.resize((int(1920 * w / h), 1920))
        bg_w, bg_h = bg.size
        bg = bg.crop(((bg_w - 1080) // 2, (bg_h - 1920) // 2, (bg_w + 1080) // 2, (bg_h + 1920) // 2))
        bg = bg.filter(ImageFilter.GaussianBlur(40))
        enhancer = ImageEnhance.Brightness(bg)
        bg = enhancer.enhance(0.35)
        canvas.paste(bg, (0, 0))
        
        fg = img.crop(crop_box)
        target_w = int(1040 * fg_scale)
        target_h = int(target_w * fg.size[1] / fg.size[0])
        if target_h > 1300:
            target_h = 1300
            target_w = int(target_h * fg.size[0] / fg.size[1])
            
        fg_resized = fg.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        shadow = Image.new("RGBA", (target_w + 40, target_h + 40), (0, 0, 0, 0))
        shadow_box = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 160))
        shadow.paste(shadow_box, (20, 20))
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        
        pos_x = (1080 - target_w) // 2
        pos_y = (1920 - target_h) // 2 + y_offset
        
        canvas.paste(shadow, (pos_x - 20, pos_y - 20), shadow)
        canvas.paste(fg_resized, (pos_x, pos_y))
        return canvas

    # Shot 1: Botella / Cristal
    shot1 = make_canvas((160, 40, 600, 560), fg_scale=0.96, y_offset=-40)
    shot1_path = ASSETS_DIR / "shop_shot1_price.jpg"
    shot1.save(shot1_path, quality=95)

    # Shot 2: Set completo con packaging de lingote
    shot2 = make_canvas((50, 40, 955, 715), fg_scale=1.0, y_offset=-60)
    shot2_path = ASSETS_DIR / "shop_shot2_gold.jpg"
    shot2.save(shot2_path, quality=95)

    # Shot 3: Cierre Mercado Pago + Envío Gratis
    shot3 = make_canvas((50, 40, 955, 715), fg_scale=0.90, y_offset=-160)
    shot3_path = ASSETS_DIR / "shop_shot3_cta.jpg"
    shot3.save(shot3_path, quality=95)

    return shot1_path, shot2_path, shot3_path

def build_video():
    print("=" * 60)
    print("🔥 ECO-MARVEX — Promo Gancho 2: Shopping vs. Árabes")
    print("=" * 60)

    shot1, shot2, shot3 = prepare_frames()

    # Guión Gancho 2
    t1 = "¿A vos te parece normal pagar cuatrocientos mil pesos por un perfume importado que a las tres horas desaparece?"
    t2 = "Los árabes sacaron este bicho con notas de café y canela que dura más de doce horas y la caja parece un lingote de oro. Es el Khamrah Qahwa original."
    t3 = "Pedilo con envío gratis a todo el país en Éco Márvex punto com con Mercado Pago. Si buscabas halagos, acá tenés."

    a1 = ASSETS_DIR / "shop_part1.mp3"
    a2 = ASSETS_DIR / "shop_part2.mp3"
    a3 = ASSETS_DIR / "shop_part3.mp3"

    dur1 = generate_tts(t1, a1, rate="+6%")
    dur2 = generate_tts(t2, a2, rate="+6%")
    dur3 = generate_tts(t3, a3, rate="+6%")
    total_dur = dur1 + dur2 + dur3

    print(f"⏱️ Duraciones: Parte 1: {dur1:.2f}s | Parte 2: {dur2:.2f}s | Parte 3: {dur3:.2f}s | Total: {total_dur:.2f}s")

    concat_list = ASSETS_DIR / "shop_audio_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{a1}'\n")
        f.write(f"file '{a2}'\n")
        f.write(f"file '{a3}'\n")

    master_audio = ASSETS_DIR / "shop_master_audio.mp3"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list), "-c", "copy", str(master_audio)
    ], "Uniendo audio master shopping")

    # Clip 1: Gancho 2
    clip1 = ASSETS_DIR / "shop_clip1.mp4"
    vf1 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0006,1.07)':d={int(dur1*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=90:color=0x7F1D1D@0.95:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='¿$400.000 POR UN PERFUME?':fontcolor=#FDE047:fontsize=64:x=(w-text_w)/2:y=120,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='QUE A LAS 3 HORAS YA NO SE SIENTE':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=210,"
        f"drawbox=y=ih-340:color=black@0.85:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='DEJA DE REGALAR TU PLATA':fontcolor=#EF4444:fontsize=54:x=(w-text_w)/2:y=h-300,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='MIRA LO QUE HICIERON LOS ARABES':fontcolor=#FEF08A:fontsize=36:x=(w-text_w)/2:y=h-200"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot1),
        "-vf", vf1, "-t", f"{dur1:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip1)
    ], "Renderizando Clip 1 (Gancho Shopping vs Árabes)")

    # Clip 2: Notas y Lingote
    clip2 = ASSETS_DIR / "shop_clip2.mp4"
    vf2 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0005,1.06)':d={int(dur2*30)}:s=1080x1920:fps=30,"
        f"drawbox=y=90:color=black@0.85:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='LATTAFA KHAMRAH QAHWA':fontcolor=#FDE047:fontsize=64:x=(w-text_w)/2:y=120,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='PACKAGING DE LUJO Y CRISTAL TALLADO':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=210,"
        f"drawbox=y=ih-340:color=black@0.85:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='DURA MAS DE 12 HORAS EN PIEL':fontcolor=#4ADE80:fontsize=52:x=(w-text_w)/2:y=h-300,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='CAFE TOSTADO - CANELA - PRALINE':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-200"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot2),
        "-vf", vf2, "-t", f"{dur2:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip2)
    ], "Renderizando Clip 2 (Lingote & Notas)")

    # Clip 3: Mercado Pago + Web
    clip3 = ASSETS_DIR / "shop_clip3.mp4"
    vf3 = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='min(zoom+0.0004,1.05)':d={int(dur3*30)}:s=1080x1920:fps=30,"
        # Mercado Pago
        f"drawbox=y=80:color=0x009EE3@0.95:width=iw:height=220:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='PAGOS SEGUROS CON MERCADO PAGO':fontcolor=white:fontsize=56:x=(w-text_w)/2:y=110,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='HASTA 3 CUOTAS Y COMPRA PROTEGIDA':fontcolor=#FEF08A:fontsize=36:x=(w-text_w)/2:y=210,"
        # Descuento
        f"drawbox=y=ih-560:color=black@0.90:width=iw:height=140:t=fill,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='10% OFF EXTRA POR TRANSFERENCIA':fontcolor=#4ADE80:fontsize=50:x=(w-text_w)/2:y=h-520,"
        # Bloque CTA Cierre
        f"drawbox=y=ih-400:color=0x1E1B4B@0.95:width=iw:height=360:t=fill,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='ENVIO GRATIS A TODO EL PAIS':fontcolor=#FDE047:fontsize=36:x=(w-text_w)/2:y=h-350,"
        f"drawtext=fontfile='{FONT_ANTON}':expansion=none:text='ecomarvex.com':fontcolor=white:fontsize=84:x=(w-text_w)/2:y=h-270,"
        f"drawtext=fontfile='{FONT_MONTSERRAT}':expansion=none:text='SI BUSCABAS HALAGOS, ACA TENES':fontcolor=#38BDF8:fontsize=34:x=(w-text_w)/2:y=h-160"
    )
    run_cmd([
        "ffmpeg", "-y", "-loop", "1", "-i", str(shot3),
        "-vf", vf3, "-t", f"{dur3:.3f}",
        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-preset", "fast", str(clip3)
    ], "Renderizando Clip 3 (Cierre Mercado Pago & Web)")

    video_list = ASSETS_DIR / "shop_video_list.txt"
    with open(video_list, "w") as f:
        f.write(f"file '{clip1}'\n")
        f.write(f"file '{clip2}'\n")
        f.write(f"file '{clip3}'\n")

    video_concat = ASSETS_DIR / "shop_video_concat.mp4"
    run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(video_list), "-c", "copy", str(video_concat)
    ], "Concatenando video shopping")

    final_output = OUTPUT_DIR / "promo_khamrah_shopping_vs_arabes_24s.mp4"
    run_cmd([
        "ffmpeg", "-y",
        "-i", str(video_concat),
        "-i", str(master_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output)
    ], "Generando video final Gancho 2")

    print("\n" + "=" * 60)
    print(f"🎉 ¡VIDEO 2 GENERADO EXITOSAMENTE!")
    print(f"📁 Ruta: {final_output}")
    size_mb = final_output.stat().st_size / (1024 * 1024)
    print(f"📊 Peso: {size_mb:.2f} MB | Duración: {total_dur:.1f}s | Resolución: 1080x1920 (9:16)")
    print("=" * 60)
    return str(final_output)

if __name__ == "__main__":
    build_video()
