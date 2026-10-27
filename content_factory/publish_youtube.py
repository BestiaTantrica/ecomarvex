#!/usr/bin/env python3
"""
Publicador automático de YouTube Shorts para EcoMarvex.
Utiliza la API oficial de Google (YouTube Data API v3) y OAuth 2.0.
"""
import os
import sys
import argparse
from pathlib import Path
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "token_youtube.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token de acceso de YouTube...")
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                print("=" * 65)
                print("⚠️  FALTA EL ARCHIVO DE CREDENCIALES DE GOOGLE")
                print("=" * 65)
                print("Para subir videos a YouTube con ecomarvex@gmail.com:")
                print("1. Entrá a https://console.cloud.google.com con ecomarvex@gmail.com")
                print("2. Creá un proyecto (ej: 'EcoMarvex Social') y activá 'YouTube Data API v3'")
                print("3. En 'Credenciales' ➔ Crear credenciales ➔ ID de cliente OAuth (Tipo: App de escritorio)")
                print("4. Descargá el JSON y guardalo en:")
                print(f"   📁 {CLIENT_SECRETS_FILE}")
                print("=" * 65)
                sys.exit(1)
                
            print("🔑 Iniciando autorización OAuth de YouTube...")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=8080)
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
            print(f"✅ Token guardado en {TOKEN_FILE}")
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_short(video_path, title, description, tags=None, privacy="public"):
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
        
    youtube = get_authenticated_service()
    
    # Asegurar etiqueta #Shorts para que YouTube lo clasifique como Short
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"
        
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or ["perfumes arabes", "ecomarvex", "khamrah qahwa", "fragancias", "argentina", "shorts"],
            "categoryId": "26"  # Howto & Style
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    print(f"🚀 Subiendo YouTube Short: {Path(video_path).name}...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Subiendo: {int(status.progress() * 100)}%")
            
    video_id = response.get("id")
    short_url = f"https://youtube.com/shorts/{video_id}"
    print("=" * 60)
    print("🎉 ¡VIDEO PUBLICADO EN YOUTUBE SHORTS!")
    print(f"🔗 Enlace: {short_url}")
    print(f"🆔 ID: {video_id}")
    print("=" * 60)
    return short_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publicador de YouTube Shorts para EcoMarvex")
    parser.add_argument("--video", type=str, default=str(BASE_DIR / "output/promo_khamrah_hook_viral_23s.mp4"), help="Ruta al video .mp4")
    parser.add_argument("--title", type=str, default="No te compres este perfume árabe si odiás llamar la atención ☕✨ #Shorts", help="Título del Short")
    parser.add_argument("--desc", type=str, default="Lattafa Khamrah Qahwa 100ml original con fijación de +12 horas. Compralo con 10% OFF y envío gratis a todo el país en https://ecomarvex.com 🇦🇷", help="Descripción")
    parser.add_argument("--privacy", type=str, choices=["public", "unlisted", "private"], default="public", help="Privacidad del video")
    
    args = parser.parse_args()
    upload_short(args.video, args.title, args.desc, privacy=args.privacy)
