#!/bin/bash

# Extrai a URL usando o Tor como SOCKS5 proxy (porta 9050) para evitar o erro 403
NEW_URL=$(yt-dlp --proxy "socks5://127.0.0.1:9050" --get-url "https://www.dailymotion.com/video/x9pha96")

if [ -n "$NEW_URL" ]; then
    ESCAPED=$(printf '%s' "$NEW_URL" | sed -e 's/[\\&|]/\\&/g')
    
    # Atualiza a linha logo a seguir ao "#EXTINF... Telepace 1" na playlist dentro da pasta streams/
    sed -i "/Telepace 1/{n;s|.*|$ESCAPED|}" streams/telepace1.m3u
    
    echo "[OK] Stream do Telepace 1 atualizado com sucesso:"
    grep -A1 "Telepace 1" streams/telepace1.m3u
else
    echo "[ERRO] Não foi possível extrair a URL com o yt-dlp."
    exit 1
fi
