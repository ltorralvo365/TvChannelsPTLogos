#!/bin/bash

# Extrai o ID do formato a 1080p e obtém a URL final num único fluxo
NEW_URL=$(yt-dlp --proxy "socks5://127.0.0.1:9050" --impersonate chrome -F "https://www.dailymotion.com/video/x9pha96" \
  | awk '!/^\[/ && /1080/ {print $1; exit}' \
  | xargs -I{} yt-dlp --proxy "socks5://127.0.0.1:9050" --impersonate chrome -f {} --get-url "https://www.dailymotion.com/video/x9pha96")

if [ -n "$NEW_URL" ]; then
    # Escapa carateres especiais (como & e /) para o sed não partir
    ESCAPED=$(printf '%s' "$NEW_URL" | sed -e 's/[\\&|]/\\&/g')
    
    # Substitui a linha a seguir ao termo "Telepace 1" em streams/playlist.m3u
    sed -i "/Telepace 1/{n;s|.*|$ESCAPED|}" streams/playlist.m3u
    
    echo "[OK] Stream 1080p extraído e injetado com sucesso:"
    grep -A1 "Telepace 1" streams/playlist.m3u
else
    echo "[ERRO] A pipeline de extração não devolveu nenhuma URL."
    exit 1
fi
