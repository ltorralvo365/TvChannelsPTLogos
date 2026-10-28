#!/usr/bin/env python3
import os
import re
import json
import urllib.request
import subprocess

VIDEO_ID = "x9qsfo8"
METADATA_URL = f"https://www.dailymotion.com/player/metadata/video/{VIDEO_ID}"
OUTPUT_M3U = "streams/telepace2.m3u8"

def get_stream_url():
    try:
        # Executa o yt-dlp para extrair diretamente a URL raw do stream .m3u8
        cmd = ["yt-dlp", "-g", METADATA_URL]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stream_url = result.stdout.strip()
        
        if stream_url.startswith("http"):
            return stream_url
        return None
    except Exception as e:
        print(f"Erro ao executar yt-dlp: {e}")
        return None

def main():
    stream_url = get_stream_url()
    
    if not stream_url:
        print("FALHA: Impossível obter a URL do stream.")
        exit(1)

    print(f"Stream encontrada: {stream_url}")

    # Layout exato de Master Playlist
    m3u_content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1465567,FRAME-RATE=50,RESOLUTION=1280x720,CODECS="avc1.64001f,mp4a.40.2"
{stream_url}
"""
    os.makedirs(os.path.dirname(OUTPUT_M3U), exist_ok=True)
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"Ficheiro {OUTPUT_M3U} atualizado!")

if __name__ == "__main__":
    main()