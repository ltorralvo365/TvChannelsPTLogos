#!/usr/bin/env python3
import re
import json
import urllib.request

VIDEO_ID = "x9pha96"
GEO_URL = f"https://geo.dailymotion.com/videos/{VIDEO_ID}"
OUTPUT_M3U = "telepace1.m3u8"  # Guardar como .m3u8

def get_stream_url():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    req = urllib.request.Request(GEO_URL, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
            
            # Tenta encontrar o player config no HTML
            match = re.search(r'__PLAYER_CONFIG__\s*=\s*(\{.+?\});', html) or \
                    re.search(r'"stream"\s*:\s*(\{\s*"stream_type".+?\})', html)
            
            if not match:
                m3u8_match = re.search(r'https://cdndirector\.dailymotion\.com/cdn/live/video/[^\s"\'\\]+', html)
                if m3u8_match:
                    return m3u8_match.group(0).replace('\\/', '/')
                raise ValueError("Não foi possível encontrar o stream no HTML")

            raw_data = match.group(1)
            if not raw_data.startswith('{'):
                raw_data = f'{{"stream":{raw_data}}}'
            
            data = json.loads(raw_data)
            if "stream" in data and "url" in data["stream"]:
                return data["stream"]["url"]
            elif "url" in data:
                return data["url"]

    except Exception as e:
        print(f"Erro ao extrair stream: {e}")
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

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"Ficheiro {OUTPUT_M3U} atualizado!")

if __name__ == "__main__":
    main()