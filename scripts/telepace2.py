#!/usr/bin/env python3
import os
import re
import json
import urllib.request

VIDEO_ID = "x9qsfo8"
METADATA_URL = f"https://www.dailymotion.com/player/metadata/video/{VIDEO_ID}"
OUTPUT_M3U = "streams/telepace2.m3u8"

def get_stream_url():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': f'https://www.dailymotion.com/embed/video/{VIDEO_ID}',
    }
    
    req = urllib.request.Request(METADATA_URL, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            # Navegar pela estrutura JSON de qualidades da Dailymotion
            qualities = data.get('qualities', {})
            if 'auto' in qualities:
                for stream in qualities['auto']:
                    if 'url' in stream:
                        return stream['url']
                        
            raise ValueError("Propriedade 'auto' ou 'url' não encontrada nos metadados")

    except Exception as e:
        print(f"Erro ao extrair stream via Player API: {e}")
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