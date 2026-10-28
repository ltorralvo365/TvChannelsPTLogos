#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPG MEO -> XMLTV
Gera epg_meo.xml com todos os canais disponiveis na API da MEO.
Sem dependencias externas (usa apenas a biblioteca padrao do Python 3.9+).
"""

import urllib.request
import urllib.parse
import json
import logging
import re
import ssl
import sys
import time
import gzip
import shutil
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape


# zoneinfo (stdlib em Python 3.9+). Se falhar, usamos fallback WET/WEST.
try:
    from zoneinfo import ZoneInfo
    _HAS_ZONEINFO = True
except Exception:  # pragma: no cover
    _HAS_ZONEINFO = False

# ============================================================
# CONFIGURACAO
# ============================================================
NR_DAYS         = 7
OUTPUT_FILE     = "epg_meogo.xml"
REQUEST_TIMEOUT = 20

baseUrl = "https://www.meo.pt"

# Mapeamento validado a partir da lista M3U fornecida.
# Chave = CallLetter MEO; valor = tvg-id Vodafone.
MEO_TO_TVG = {'RTP1': 'RTP1.pt', 'RTP2': 'RTP2.pt', 'SIC': 'SIC.pt', 'TVI': 'TVI.pt', 'SICN': 'SICNoticias.pt', 'RTPN': 'RTPNoticias.pt', 'CNNPT': 'CNNPortugal.pt', 'CMTV': 'CMTV.pt', 'NEWSNOW': 'NewsNow.pt', 'GLOB': 'Globo.pt', 'C11': 'Canal11.pt', 'VMAISTVI': 'VPlusTVI.pt', 'PORTO': 'PortoCanal.pt', 'SICC': 'SICCaras.pt', 'SICR': 'SICRadical.pt', 'SICM': 'SICMulher.pt', 'SICNOV': 'SICNovelas.pt', 'RTPM': 'RTPMemoria.pt', 'SPTVHD': 'SportTVPlus.pt', 'SPT1HD': 'SportTV1.pt', 'SPT2HD': 'SportTV2.pt', 'SPT3HD': 'SportTV3.pt', 'SPT4HD': 'SportTV4.pt', 'SPT5HD': 'SportTV5.pt', 'SPT6HD': 'SportTV6.pt', 'SPT7HD': 'SportTV7.pt', 'EURHD': 'Eurosport1.pt', 'EURS2HD': 'Eurosport2.pt', 'ABOLA': 'ABolaTV.pt', 'SLBHD': 'BenficaTV.pt', 'SCPHD': 'SportingTV.pt', 'DAZN1': 'DAZN1.pt', 'DAZN2': 'DAZN2.pt', 'DAZN3': 'DAZN3.pt', 'DAZN4': 'DAZN4.pt', 'DAZN5': 'DAZN5.pt', 'DISNY': 'DisneyChannel.pt', 'DISNYJ': 'DisneyJunior.pt', 'PANDAK': 'PandaKids.pt', 'CART': 'CartoonNetwork.pt', 'PANDA': 'CanalPanda.pt', 'BABYT': 'BabyTV.uk', 'SICK': 'SICK.pt', 'NICKELO': 'Nickelodeon.pt', 'DIZI': 'TimelessDiziChannel.ro', 'TVCTOPH': 'TVCineTop.pt', 'TVCEDIH': 'TVCineEdition.pt', 'TVCEMOH': 'TVCineEmotion.pt', 'TVCACTH': 'TVCineAction.pt', 'HOLHD': 'CanalHollywood.pt', 'CINEHD': 'CineMundo.pt', 'STARMOV': 'StarMovies.pt', 'STARCHA': 'StarChannel.pt', 'AXNHD': 'AXN.pt', 'STARLIF': 'StarLife.pt', 'STARCRI': 'StarCrime.pt', 'STARCOM': 'StarComedy.pt', 'AXWHD': 'AXNWhite.pt', 'AXNMHD': 'AXNMovies.pt', 'SYFHD': 'Syfy.pt', 'AMCHD': 'AMC.pt', 'QHD': 'CanalQ.pt', 'MCMTHD': 'MCMTop.fr', 'MCM P': 'MCMPop.fr', 'AFRO': 'AfroMusic.pt', 'MEZHD': 'MezzoLive.fr', '24KTHD': '24Kitchen.pt', 'CASACOZ': 'CasaeCozinha.pt', 'DISCVHD': 'DiscoveryChannel.pt', 'NGHD': 'NationalGeographic.pt', 'WILDHD': 'NationalGeographicWild.pt', 'HISTHD': 'Historia.pt', 'ODISSHD': 'Odisseia.pt', 'AMCCRI': 'AMCCrime.pt', 'SMAISHD': 'SPlus.pt', 'TVIR': 'TVIReality.pt', 'REC HD': 'RecordTVEuropa.pt', 'AMCBRE': 'AMCBreak.pt', 'TLC': 'TLC.pt', 'FTVHD': 'FashionTVEurope.fr', 'GAMET': 'Gametoon.nl', 'ARTV': 'ARTV.pt', 'RECNEW': 'recordnews.pt', 'CNN': 'CNNInternational.us', 'EURN': 'EuronewsPortuguese.fr', 'BLOOM': 'BloombergTV.us', 'SKYN': 'SkyNewsInternational.uk', 'CNBC': 'CNBC.pt', 'ALJAZHD': 'AlJazeera.qa', 'TVE24HD': 'TVE24h.pt', 'FR24F': 'France24French.fr', 'FR24I': 'France24Espanol.fr', 'RTPMA': 'RTPMadeira.pt', 'RTPACR': 'RTPAcores.pt', 'LVTVHD': 'LocalVisaoTV.pt', 'RTPA': 'RTPAfrica.pt', 'TPA': 'TPA.ao', 'TVGAL': 'GaliciaTVEuropa.es', 'TVEIHD': 'TVEi.pt', 'TV5HD': 'TV5Monde.fr', 'RAI1': 'rai1.it', 'KBS': 'KBSWorld.kr', 'ARIRANG': 'ArirangTv.kr', 'NHKHD': 'NHKWorldJapan.jp', 'FREEDOM': 'Freedom.ua', 'CNOVA': 'TVCancaoNova.pt', 'UNIFE': 'UniFe.pt', 'KURIAKO': 'KuriakosTV.pt'}

ssl._create_default_https_context = ssl._create_unverified_context


# ============================================================
# CLASSES XMLTV
# ============================================================
class Channel:
    def __init__(self, id, display_name, lang="pt", icon_src=None):
        self.id = id
        self.display_name = display_name
        self.lang = lang
        self.icon_src = icon_src
        self.url = None

    def setUrl(self, url):
        self.url = url

    def getId(self):
        return self.id

    def getDisplayName(self):
        return self.display_name

    def getIconSrc(self):
        return self.icon_src

    def to_xml(self):
        icon = f'<icon src="{escape(self.icon_src)}" />' if self.icon_src else ""
        url  = f'<url>{escape(self.url)}</url>' if self.url else ""
        return (
            f'  <channel id="{escape(self.id)}">\n'
            f'    <display-name lang="{self.lang}">{escape(self.display_name)}</display-name>\n'
            f'    {icon}\n'
            f'    {url}\n'
            f'  </channel>'
        )


class Programme:
    def __init__(self, channel_id, start, stop, title, desc="", lang="pt", icon=None):
        self.channel_id = channel_id
        self.start = start
        self.stop = stop
        self.title = title
        self.desc = desc
        self.lang = lang
        self.icon = icon
        self.season = None
        self.episode = None

    def setSeasonNumber(self, season):
        self.season = season

    def setEpisodeNumber(self, episode):
        self.episode = episode

    def to_xml(self):
        parts = [
            f'  <programme start="{self.start}" stop="{self.stop}" channel="{escape(self.channel_id)}">',
            f'    <title lang="{self.lang}">{escape(self.title)}</title>',
        ]
        if self.desc:
            parts.append(f'    <desc lang="{self.lang}">{escape(self.desc)}</desc>')
        if self.icon:
            parts.append(f'    <icon src="{escape(self.icon)}" />')
        if self.season is not None:
            s = max(int(self.season) - 1, 0)
            e = max(int(self.episode) - 1, 0) if self.episode else 0
            parts.append(f'    <episode-num system="xmltv_ns">{s}.{e}.0/1</episode-num>')
        elif self.episode is not None:
            e = max(int(self.episode) - 1, 0)
            parts.append(f'    <episode-num system="xmltv_ns">0.{e}.0/1</episode-num>')
        parts.append('  </programme>')
        return "\n".join(parts)


class XMLTV:
    def __init__(self):
        self.channels = []
        self.programmes = []

    def addChannel(self, channel):
        self.channels.append(channel)

    def addProgramme(self, programme):
        self.programmes.append(programme)

    def to_xml(self):
        header = '<?xml version="1.0" encoding="UTF-8"?>\n<tv generator-info-name="meo-epg">\n'
        body  = "\n".join(c.to_xml() for c in self.channels)
        body += "\n\n" + "\n".join(p.to_xml() for p in self.programmes)
        return header + body + "\n</tv>\n"

    def write(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.to_xml())


# ============================================================
# TIMEZONE (Europe/Lisbon com fallback)
# ============================================================
def _lisbon_tz():
    if _HAS_ZONEINFO:
        try:
            return ZoneInfo("Europe/Lisbon")
        except Exception:
            pass
    # Fallback: WET/WEST manual (Portugal Continental)
    logging.warning("zoneinfo indisponivel; a usar fallback WET/WEST. "
                    "Instala 'tzdata' (pip install tzdata) para mais precisao.")
    return timezone(timedelta(hours=0))


# ============================================================
# HTTP
# ============================================================
def _http_get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            'Origin': 'https://www.meo.pt',
            'Referer': 'https://www.meo.pt/',
            'User-Agent': ('Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/144.0.0.0 Mobile Safari/537.36'),
            'Accept': '*/*',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            if resp.getcode() != 200:
                logging.warning("HTTP %s em %s", resp.getcode(), url)
                return None
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        logging.error("Pedido HTTP falhou: %s (%s)", e, url)
        return None


def _get_supported_channels():
    """Devolve lista de dicts {callLetter, name, icon} para os canais da MEO."""
    url = ("https://meogouser.apps.meo.pt/Services/GridTv/GridTv.svc/"
           "GetContentsForChannels?userAgent=IPTV_OFR_GTV")
    data = _http_get_json(url)
    if not data or data.get("Status") != "OK":
        logging.error("Resposta invalida de GetContentsForChannels: %s",
                      (data or {}).get("Status"))
        return []

    result = []
    for ch in data.get("Result", []):
        call = ch.get("CallLetter")
        if not call:
            continue
        name = (ch.get("Name") or ch.get("Title") or ch.get("ChannelName")
                or ch.get("Description") or call)
        icon = None
        for field in ("LogoUrl", "LinkToLogo", "Logo", "Image", "ImageUrl"):
            v = ch.get(field)
            if isinstance(v, str) and v:
                icon = v
                break
        result.append({"callLetter": call, "name": name, "icon": icon})

    return result


def _get_programs_for_channel(call_letter, date_str):
    url = ("https://meogouser.apps.meo.pt/Services/GridTv/GridTv.svc/"
           f"GetLiveChannelProgramsByDate?callLetter={urllib.parse.quote(call_letter)}"
           f"&date={date_str}&userAgent=IPTV_OFR_GTV")
    data = _http_get_json(url)
    if not data or data.get("Status") != "OK":
        return []
    return data.get("Result", []) or []


# ============================================================
# PARSING
# ============================================================
_DATE_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S",
)


def _parse_naive_utc(s):
    """Faz parse de uma string ISO de data UTC (sem timezone) -> datetime naive."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"formato de data desconhecido: {s!r}")


def _to_xmltv_time(s, tz):
    """Converte string UTC da MEO para 'YYYYMMDDHHMMSS +0000' em hora de Lisboa."""
    naive = _parse_naive_utc(s)
    loc   = naive.replace(tzinfo=timezone.utc).astimezone(tz)
    return loc.strftime("%Y%m%d%H%M%S %z")


def _find_season_episode(title, p):
    m = re.match(r'.*(\s+|:)T(\d+)(?:\s+-?\s*Ep\.\s*)?(\d+)?$', title)
    if m:
        if m.group(2):
            p.setSeasonNumber(m.group(2))
        if m.group(3):
            p.setEpisodeNumber(m.group(3))
        return
    m = re.match(r'.*\s+Ep\.\s*(\d+)$', title)
    if m and m.group(1):
        p.setEpisodeNumber(m.group(1))


def _build_icon(call_letter, title):
    if not title:
        return None
    return ("https://cdn-er-images.online.meo.pt/eemstb/ImageHandler.ashx"
            f"?chCallLetter={urllib.parse.quote(call_letter)}"
            f"&progTitle={urllib.parse.quote(title)}"
            "&profile=16_9&profileFallback=false&noFallback=true"
            "&appSource=PC_CHROME_PWA&width=1920&csf")


# ============================================================
# MAIN
# ============================================================
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    tz    = _lisbon_tz()
    xmltv = XMLTV()

    # ---------- 1. Canais ----------
    logging.info("A obter lista de canais da MEO...")
    channels = _get_supported_channels()
    if not channels:
        logging.error("Nenhum canal obtido. A abortar.")
        sys.exit(1)
    logging.info("Recebidos %d canais.", len(channels))

    channels = [ch for ch in channels if ch["callLetter"] in MEO_TO_TVG]
    for ch in channels:
        c = Channel(MEO_TO_TVG[ch["callLetter"]], ch["name"], "pt", ch["icon"])
        c.setUrl(baseUrl)
        xmltv.addChannel(c)

    # ---------- 2. EPG por canal ----------
    today = datetime.now(tz)
    days  = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(NR_DAYS, -1, -1)]

    total_programmes = 0
    errors = 0

    for idx, ch in enumerate(channels, start=1):
        call = ch["callLetter"]
        logging.info("[%d/%d] EPG -> %s (%s)", idx, len(channels), ch["name"], call)

        for date_str in days:
            programs = _get_programs_for_channel(call, date_str)
            if not programs:
                continue

            for prog in programs:
                try:
                    s_time = _to_xmltv_time(prog["StartDate"], tz)
                    e_time = _to_xmltv_time(prog["EndDate"],   tz)
                except Exception as e:
                    logging.debug("  Erro a fazer parse de datas: %s", e)
                    continue

                title = prog.get("Title") or "Sem titulo"
                desc  = prog.get("Synopsis") or prog.get("Description") or ""
                icon  = _build_icon(call, title)

                p = Programme(MEO_TO_TVG[call], s_time, e_time, title, desc, "pt", icon)
                _find_season_episode(title, p)
                xmltv.addProgramme(p)
                total_programmes += 1

            time.sleep(0.1)  # pequena pausa entre dias

    # ---------- 3. Guardar ----------
    logging.info("A guardar %s ...", OUTPUT_FILE)
    xmltv.write(OUTPUT_FILE)

    # Comprimir o XMLTV completo automaticamente para .gz.
    gz_file = OUTPUT_FILE + ".gz"
    logging.info("A comprimir %s ...", gz_file)
    with open(OUTPUT_FILE, "rb") as origem:
        with gzip.open(gz_file, "wb", compresslevel=9) as destino:
            shutil.copyfileobj(origem, destino)
    logging.info("EPG comprimido criado: %s", gz_file)

    logging.info("Concluido: %d canais, %d programas, %d canais com erro.",
                 len(channels), total_programmes, errors)


if __name__ == "__main__":
    main()