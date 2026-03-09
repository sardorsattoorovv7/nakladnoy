import os
import math
import json
import html
from pathlib import Path
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# PAGE
# =========================================================
st.set_page_config(
    page_title="EcoProm Pro Konstruktor",
    layout="wide",
    page_icon="🏗"
)

# =========================================================
# CONSTANTS
# =========================================================
TELEGRAM_CHAT_ID = "-1002338157363"
DATA_FILE = Path("ecoprom_form_data.json")

DEFAULT_FORM_DATA = {
    "L_text": "5",
    "W_text": "4",
    "H_text": "3",
    "d_turi": "Sovutgich (PIR)",
    "d_qalin": "100mm",
    "p_turi": "Sovutgich (PIR)",
    "p_qalin": "80mm",
    "panel_width_m": 1.16,
    "pol_bor": True,
    "pol_turi": "PIR (Standart)",
    "pol_qalin": "100mm",
    "eshik": "Muzlatkich eshigi",
    "eshik_joyi": "Old",
    "eshik_pozitsiya": "O'rta",
    "eshik_ochilish": "Ichkariga",
    "agregat": "Split-sistema (Nizkotemp)",
    "agregat_joyi": "Old",
    "project_name": "",
    "room_code": "EP-001",
    "mahsulot_turi": "Go'sht",
    "saqlash_temp": "-18°C",
    "ochilish_soni": "Kam",
    "hudud": "Mo'tadil",
    "namlik_talabi": "Standart",
    "ag_brand": "Bitzer",
    "montaj_progress": 100,
    "show_3d_labels": True,
}

# =========================================================
# OPTIONS
# =========================================================
d_turi_options = ["Sovutgich (PIR)", "Oddiy Devor", "Sendvich Mineral paxta"]
d_qalin_options = ["50mm", "80mm", "100mm", "120mm", "150mm", "200mm"]
p_turi_options = ["Sovutgich (PIR)", "Tom uchun (Trapsiya)", "Tekis panel"]
p_qalin_options = ["50mm", "80mm", "100mm", "120mm", "150mm"]
panel_width_options = [0.96, 1.00, 1.16]
pol_turi_options = ["PIR (Kuchaytirilgan)", "PIR (Standart)"]
pol_qalin_options = ["50mm", "80mm", "100mm", "120mm", "150mm"]
eshik_options = ["Yo'q", "Bir tabaqali (90x190)", "Surilma (120x200)", "Muzlatkich eshigi"]
eshik_joyi_options = ["Old", "Orqa", "O'ng", "Chap"]
eshik_ochilish_options = ["Ichkariga", "Tashqariga"]
agregat_options = ["Yo'q", "Mono-blok (Srednetemp)", "Split-sistema (Nizkotemp)", "Zanotti (Italiya)"]
agregat_joyi_options = ["Old", "Orqa", "O'ng", "Chap"]
mahsulot_options = [
    "Go'sht", "Tovuq", "Baliq", "Muzqaymoq", "Sut mahsulotlari",
    "Meva-sabzavot", "Gullar", "Dorilar", "Ichimliklar", "Aralash mahsulot"
]
ochilish_options = ["Kam", "O'rtacha", "Ko'p"]
hudud_options = ["Sovuq", "Mo'tadil", "Issiq"]
namlik_options = ["Standart", "Past namlik", "Yuqori namlik"]
eshik_side_position_options = ["Tepa", "O'rta", "Past"]
eshik_topbottom_position_options = ["Chap", "O'rta", "O'ng"]
ag_brand_options = ["Bitzer", "Zanotti", "Frascold", "Copeland"]

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
.main {
    background: #ececec;
}
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}
h1, h2, h3, h4 {
    color: #111111;
}
.stButton > button {
    width: 100%;
    border-radius: 10px;
    height: 2.9em;
    background: #111111;
    color: white;
    font-weight: 700;
    border: none;
}
.stDownloadButton > button {
    width: 100%;
    border-radius: 10px;
    height: 2.9em;
    background: #1f2937;
    color: white;
    font-weight: 700;
    border: none;
}
.report-box,
.metric-box,
.tech-table,
.ai-box,
.spec-card,
.side-card {
    background: white;
    border-radius: 14px;
    border: 1px solid #d9d9d9;
    box-shadow: 0 1px 0 rgba(0,0,0,0.03);
}
.report-box { padding: 22px; }
.metric-box { padding: 16px; text-align: center; min-height: 96px; }
.tech-table { padding: 18px; height: 100%; }
.ai-box { padding: 18px; border-left: 6px solid #333; }
.spec-card { padding: 18px; margin-bottom: 12px; }
.side-card { padding: 15px; margin-bottom: 10px; }
.metric-title {
    color: #666;
    font-size: 13px;
}
.metric-value {
    color: #111;
    font-size: 24px;
    font-weight: 800;
    margin-top: 8px;
}
small, .stCaption {
    color: #666 !important;
}
hr {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    font-size: 12px;
    margin-right: 6px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# PERSISTENCE
# =========================================================
def load_form_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULT_FORM_DATA.copy()
            merged.update(data)
            return merged
        except Exception:
            return DEFAULT_FORM_DATA.copy()
    return DEFAULT_FORM_DATA.copy()


def save_form_data():
    data = {}
    for key in DEFAULT_FORM_DATA.keys():
        data[key] = st.session_state.get(key, DEFAULT_FORM_DATA[key])

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.warning(f"Saqlashda xatolik: {e}")


def init_form_state():
    data = load_form_data()
    for key, value in data.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_form_state()

# =========================================================
# HELPERS
# =========================================================
def parse_dim(text: str):
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        val = float(text)
        if val <= 0:
            return None
        return val
    except Exception:
        return None


def mm_val(s: str) -> int:
    return int(str(s).replace("mm", "").strip())


def m_to_mm(m: float) -> int:
    return int(round(m * 1000))


def fmt_m(v: float) -> str:
    return f"{v:.2f} m"


def fmt_mm(v: int) -> str:
    return f"{int(v)} mm"


def clamp(v, low, high):
    return max(low, min(v, high))


def door_dimensions(eshik: str):
    if eshik == "Bir tabaqali (90x190)":
        return 900, 1900
    elif eshik == "Surilma (120x200)":
        return 1200, 2000
    elif eshik == "Muzlatkich eshigi":
        return 960, 2000
    return 0, 0


def panel_count_linear(length_m, panel_width_m=1.16):
    full = int(length_m // panel_width_m)
    rem = round(length_m - (full * panel_width_m), 3)
    total = full + (1 if rem > 0.01 else 0)
    return {
        "full_panels": full,
        "remainder_m": rem,
        "total_panels": total
    }


def material_palette(panel_name: str):
    return {
        "panel": "#FFFFFF",
        "edge": "#C9CED6",
        "door": "#2B2B2B",
        "aggr": "#C0392B",
        "floor": "#F7F7F7",
        "logo": "#16A34A"
    }


def get_colors():
    return {
        "page": "#f2f2f2",
        "sheet": "#ffffff",
        "line": "#111111",
        "thin": "#444444",
        "dim": "#222222",
        "text": "#111111",
        "muted": "#555555",
        "door": "#111111",
        "accent": "#111111"
    }


def draw_svg(svg_code: str, height: int = 1080):
    html_code = f"""
    <div style="width:100%; background:#dcdcdc; padding:16px; overflow:auto; border-radius:12px;">
        {svg_code}
    </div>
    """
    components.html(html_code, height=height, scrolling=True)

# =========================================================
# TELEGRAM
# =========================================================
def telegram_escape_html(text: str) -> str:
    return html.escape(str(text), quote=False)


def build_telegram_message(data: dict) -> str:
    top_report = " + ".join(
        [f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in data["top_meta"]]
    )
    right_report = " + ".join(
        [f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in data["right_meta"]]
    )

    ai_block = ""
    if data.get("ai_data"):
        ai = data["ai_data"]
        ai_block = f"""

<b>🤖 AI Tavsiya</b>
• Rejim: {telegram_escape_html(ai.get("rejim", "-"))}
• Devor: {telegram_escape_html(ai.get("devor_qalinligi_mm", "-"))} mm
• Patalok: {telegram_escape_html(ai.get("patalok_qalinligi_mm", "-"))} mm
• Pol: {telegram_escape_html(ai.get("pol_qalinligi_mm", "-"))} mm
• Agregat: {telegram_escape_html(ai.get("agregat_turi", "-"))}
• Eshik: {telegram_escape_html(ai.get("eshik_turi", "-"))}
• Izoh: {telegram_escape_html(ai.get("izoh", "-"))}
• Xulosa: {telegram_escape_html(ai.get("xulosa", "-"))}
"""

    msg = f"""
<b>🏗 Yangi buyurtma / loyiha</b>

<b>Loyiha:</b> {telegram_escape_html(data["project_name"])}
<b>Kod:</b> {telegram_escape_html(data["room_code"])}
<b>Sana:</b> {telegram_escape_html(datetime.now().strftime("%d.%m.%Y %H:%M"))}

<b>Tashqi o'lcham:</b> {telegram_escape_html(data["L"])} × {telegram_escape_html(data["W"])} × {telegram_escape_html(data["H"])} m
<b>Ichki foydali o'lcham:</b> {data["inner_L_mm"]} × {data["inner_W_mm"]} × {data["inner_H_mm"]} mm
<b>Hajm:</b> {data["hajm"]} m³

<b>Devor:</b> {telegram_escape_html(data["d_turi"])} / {data["wall_mm"]} mm / {data["s_devor"]} m²
<b>Patalok:</b> {telegram_escape_html(data["p_turi"])} / {data["ceil_mm"]} mm / {data["s_patalok"]} m²
<b>Pol:</b> {telegram_escape_html(data["pol_turi"] if data["pol_bor"] else "Mavjud emas")} / {data["floor_mm"] if data["pol_bor"] else 0} mm / {data["s_pol"]} m²

<b>Eshik:</b> {telegram_escape_html(data["eshik"])}
<b>Eshik joylashuvi:</b> {telegram_escape_html(data["eshik_joyi"])}
<b>Eshik pozitsiyasi:</b> {telegram_escape_html(data["eshik_pozitsiya"])}
<b>Eshik ochilishi:</b> {telegram_escape_html(data["eshik_ochilish"])}

<b>Agregat:</b> {telegram_escape_html(data["agregat"])}
<b>Agregat joylashuvi:</b> {telegram_escape_html(data["agregat_joyi"])}

<b>Uzunlik segmentlari:</b> {telegram_escape_html(top_report)}
<b>En segmentlari:</b> {telegram_escape_html(right_report)}

<b>Panel ishchi eni:</b> {data["panel_width_m"]} m
<b>Umumiy devor paneli:</b> {data["devor_panels_total"]} ta
<b>Patalok paneli:</b> {data["patalok_panels_total"]} ta
<b>Pol paneli:</b> {data["pol_panels_total"] if data["pol_bor"] else 0} ta
{ai_block}
""".strip()

    return msg


def send_to_telegram_channel(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return False, "TELEGRAM_BOT_TOKEN topilmadi"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            return False, f"Telegram xatolik: {r.text}"
        return True, "Yuborildi"
    except Exception as e:
        return False, f"Telegram yuborishda xatolik: {e}"

# =========================================================
# GROQ AI
# =========================================================
def get_groq_recommendation(
    mahsulot_turi,
    saqlash_temp,
    ochilish_soni,
    hudud,
    namlik_talabi,
    L,
    W,
    H,
    pol_bor
):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return {
            "success": False,
            "message": "GROQ_API_KEY topilmadi. .env yoki system env ga qo'ying."
        }

    prompt = f"""
Siz sovutish kamerasi bo'yicha professional muhandissiz.
Foydalanuvchiga texnik tavsiya bering.

Mijoz ma'lumotlari:
- Mahsulot turi: {mahsulot_turi}
- Talab qilinadigan harorat: {saqlash_temp}
- Kunlik eshik ochilish soni: {ochilish_soni}
- Hudud / iqlim: {hudud}
- Namlik talabi: {namlik_talabi}
- O'lcham: {L}m x {W}m x {H}m
- Pol paneli: {"Ha" if pol_bor else "Yo'q"}

JSON formatda qaytaring:
{{
  "rejim": "...",
  "devor_qalinligi_mm": 100,
  "patalok_qalinligi_mm": 80,
  "pol_qalinligi_mm": 100,
  "agregat_turi": "...",
  "eshik_turi": "...",
  "izoh": "...",
  "xulosa": "..."
}}

Faqat JSON qaytaring.
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "Siz texnik sovutish kamerasi mutaxassisisiz."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]

        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return {"success": False, "message": f"JSON parse bo'lmadi: {content}"}

        parsed = json.loads(content[start:end + 1])
        return {"success": True, "data": parsed}

    except Exception as e:
        return {"success": False, "message": f"Groq xatolik: {e}"}

# =========================================================
# SVG UTILS
# =========================================================
def svg_text(x, y, text, size=12, weight="normal", anchor="middle", rotate=None, color="#111"):
    if rotate is not None:
        return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}" transform="rotate({rotate} {x},{y})">{text}</text>'
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{color}">{text}</text>'


def dim_h(x1, x2, y, text, color="#222", ext=8, size=11):
    return f"""
    <g stroke="{color}" fill="none" stroke-width="1">
        <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" />
        <line x1="{x1}" y1="{y-ext}" x2="{x1}" y2="{y+ext}" />
        <line x1="{x2}" y1="{y-ext}" x2="{x2}" y2="{y+ext}" />
        <polygon points="{x1},{y} {x1+6},{y-3} {x1+6},{y+3}" fill="{color}" />
        <polygon points="{x2},{y} {x2-6},{y-3} {x2-6},{y+3}" fill="{color}" />
    </g>
    <text x="{(x1+x2)/2}" y="{y-8}" font-size="{size}" text-anchor="middle" fill="{color}">{text}</text>
    """


def dim_v(x, y1, y2, text, color="#222", ext=8, size=11):
    cy = (y1 + y2) / 2
    return f"""
    <g stroke="{color}" fill="none" stroke-width="1">
        <line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" />
        <line x1="{x-ext}" y1="{y1}" x2="{x+ext}" y2="{y1}" />
        <line x1="{x-ext}" y1="{y2}" x2="{x+ext}" y2="{y2}" />
        <polygon points="{x},{y1} {x-3},{y1+6} {x+3},{y1+6}" fill="{color}" />
        <polygon points="{x},{y2} {x-3},{y2-6} {x+3},{y2-6}" fill="{color}" />
    </g>
    <text x="{x+15}" y="{cy}" font-size="{size}" text-anchor="middle" fill="{color}" transform="rotate(90 {x+15},{cy})">{text}</text>
    """


def chain_dim_top(x, y, parts, scale, color="#222"):
    svg = ""
    total = sum(p["size"] for p in parts)
    svg += dim_h(x, x + total * scale, y - 24, f"{total}", color=color, size=12)

    cur = x
    for p in parts:
        nx = cur + p["size"] * scale
        label = f'{p["size"]} ESHIK' if p["type"] == "door" else str(p["size"])
        svg += f'<line x1="{cur}" y1="{y}" x2="{cur}" y2="{y-8}" stroke="{color}" stroke-width="1"/>'
        svg += f'<line x1="{nx}" y1="{y}" x2="{nx}" y2="{y-8}" stroke="{color}" stroke-width="1"/>'
        svg += f'<line x1="{cur}" y1="{y}" x2="{nx}" y2="{y}" stroke="{color}" stroke-width="1"/>'
        svg += f'<text x="{(cur+nx)/2}" y="{y-6}" font-size="10" text-anchor="middle" fill="{color}">{label}</text>'
        cur = nx

    return svg


def chain_dim_right(x, y, parts, scale, color="#222"):
    svg = ""
    total = sum(p["size"] for p in parts)
    svg += dim_v(x + 24, y, y + total * scale, f"{total}", color=color, size=12)

    cur = y
    for p in parts:
        ny = cur + p["size"] * scale
        label = f'{p["size"]} ESHIK' if p["type"] == "door" else str(p["size"])
        svg += f'<line x1="{x}" y1="{cur}" x2="{x+8}" y2="{cur}" stroke="{color}" stroke-width="1"/>'
        svg += f'<line x1="{x}" y1="{ny}" x2="{x+8}" y2="{ny}" stroke="{color}" stroke-width="1"/>'
        svg += f'<line x1="{x}" y1="{cur}" x2="{x}" y2="{ny}" stroke="{color}" stroke-width="1"/>'
        svg += f'<text x="{x+12}" y="{(cur+ny)/2}" font-size="10" text-anchor="middle" fill="{color}" transform="rotate(90 {x+12},{(cur+ny)/2})">{label}</text>'
        cur = ny

    return svg


def draw_segment_ticks_top(x, y, parts, scale, color="#111"):
    svg = ""
    cur = x
    for p in parts[:-1]:
        cur += p["size"] * scale
        svg += f'<line x1="{cur}" y1="{y-4}" x2="{cur}" y2="{y+4}" stroke="{color}" stroke-width="1"/>'
    return svg


def draw_segment_ticks_right(x, y, parts, scale, color="#111"):
    svg = ""
    cur = y
    for p in parts[:-1]:
        cur += p["size"] * scale
        svg += f'<line x1="{x-4}" y1="{cur}" x2="{x+4}" y2="{cur}" stroke="{color}" stroke-width="1"/>'
    return svg

# =========================================================
# SEGMENT LOGIC
# =========================================================
def split_center_by_960(center_mm: int, module_mm: int = 960):
    if center_mm <= 0:
        return []

    parts = []
    remain = center_mm

    while remain > module_mm:
        next_remain = remain - module_mm
        if next_remain <= module_mm:
            parts.append(module_mm)
            remain = next_remain
            break
        parts.append(module_mm)
        remain -= module_mm

    if remain > 0:
        parts.append(remain)

    return parts


def build_side_segments(total_mm: int, corner_mm: int = 480, module_mm: int = 960):
    if total_mm <= 0:
        return []
    if total_mm <= corner_mm * 2:
        return [total_mm]

    center_mm = total_mm - (corner_mm * 2)
    center_parts = split_center_by_960(center_mm, module_mm)
    return [corner_mm] + center_parts + [corner_mm]


def segment_meta(parts, has_door=False, door_size=960):
    result = []
    door_used = False

    for p in parts:
        if has_door and (not door_used) and p == door_size:
            result.append({"size": p, "type": "door"})
            door_used = True
        else:
            result.append({"size": p, "type": "panel"})
    return result


def get_door_offset_mm(parts, position, side_type="vertical", door_size_mm=960):
    total = sum(parts)
    if total <= 0:
        return 0

    if side_type == "vertical":
        if position == "Tepa":
            offset = 480
        elif position == "Past":
            offset = total - 480 - door_size_mm
        else:
            offset = (total - door_size_mm) / 2
    else:
        if position == "Chap":
            offset = 480
        elif position == "O'ng":
            offset = total - 480 - door_size_mm
        else:
            offset = (total - door_size_mm) / 2

    return int(clamp(offset, 0, max(0, total - door_size_mm)))

# =========================================================
# DRAWING DETAILS
# =========================================================
def room_plan_svg(x, y, outer_w, outer_h, wall_t, colors=None):
    c = colors or get_colors()
    inner_x = x + wall_t
    inner_y = y + wall_t
    inner_w = outer_w - 2 * wall_t
    inner_h = outer_h - 2 * wall_t

    return f"""
    <rect x="{x}" y="{y}" width="{outer_w}" height="{outer_h}" fill="none" stroke="{c['line']}" stroke-width="1.6"/>
    <rect x="{inner_x}" y="{inner_y}" width="{inner_w}" height="{inner_h}" fill="none" stroke="{c['line']}" stroke-width="1.1"/>
    """


def slab_svg(x, y, outer_w, outer_h, vertical_parts_meta, scale, left_label, colors=None):
    c = colors or get_colors()

    svg = f'<rect x="{x}" y="{y}" width="{outer_w}" height="{outer_h}" fill="none" stroke="{c["line"]}" stroke-width="1.4"/>'

    cur = y
    for s in vertical_parts_meta[:-1]:
        cur += s["size"] * scale
        svg += f'<line x1="{x}" y1="{cur}" x2="{x+outer_w}" y2="{cur}" stroke="{c["line"]}" stroke-width="1"/>'

    svg += svg_text(x - 26, y + outer_h/2, left_label, size=18, rotate=90, color=c["text"])
    return svg


def draw_door_left(x, y, scale, door_offset_mm, door_h_mm=2000, opening="Ichkariga", colors=None):
    c = colors or get_colors()

    top = y + door_offset_mm * scale
    bot = top + door_h_mm * scale

    if opening == "Ichkariga":
        return f"""
        <line x1="{x}" y1="{top}" x2="{x+22}" y2="{top+32}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{x}" y1="{bot}" x2="{x+22}" y2="{bot-32}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{x+22}" y1="{top+32}" x2="{x+22}" y2="{bot-32}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{x}" y1="{top}" x2="{x-22}" y2="{top-32}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{x}" y1="{bot}" x2="{x-22}" y2="{bot+32}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{x-22}" y1="{top-32}" x2="{x-22}" y2="{bot+32}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_right(x, y, outer_w, scale, door_offset_mm, door_h_mm=2000, opening="Ichkariga", colors=None):
    c = colors or get_colors()
    rx = x + outer_w

    top = y + door_offset_mm * scale
    bot = top + door_h_mm * scale

    if opening == "Ichkariga":
        return f"""
        <line x1="{rx}" y1="{top}" x2="{rx-22}" y2="{top+32}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{rx}" y1="{bot}" x2="{rx-22}" y2="{bot-32}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{rx-22}" y1="{top+32}" x2="{rx-22}" y2="{bot-32}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{rx}" y1="{top}" x2="{rx+22}" y2="{top-32}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{rx}" y1="{bot}" x2="{rx+22}" y2="{bot+32}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{rx+22}" y1="{top-32}" x2="{rx+22}" y2="{bot+32}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_top(x, y, scale, door_offset_mm, door_w_mm=960, opening="Ichkariga", colors=None):
    c = colors or get_colors()

    left = x + door_offset_mm * scale
    right = left + door_w_mm * scale

    if opening == "Ichkariga":
        return f"""
        <line x1="{left}" y1="{y}" x2="{left+32}" y2="{y+22}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{right}" y1="{y}" x2="{right-32}" y2="{y+22}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{left+32}" y1="{y+22}" x2="{right-32}" y2="{y+22}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{left}" y1="{y}" x2="{left-32}" y2="{y-22}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{right}" y1="{y}" x2="{right+32}" y2="{y-22}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{left-32}" y1="{y-22}" x2="{right+32}" y2="{y-22}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_bottom(x, y, outer_h, scale, door_offset_mm, door_w_mm=960, opening="Ichkariga", colors=None):
    c = colors or get_colors()
    by = y + outer_h

    left = x + door_offset_mm * scale
    right = left + door_w_mm * scale

    if opening == "Ichkariga":
        return f"""
        <line x1="{left}" y1="{by}" x2="{left+32}" y2="{by-22}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{right}" y1="{by}" x2="{right-32}" y2="{by-22}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{left+32}" y1="{by-22}" x2="{right-32}" y2="{by-22}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{left}" y1="{by}" x2="{left-32}" y2="{by+22}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{right}" y1="{by}" x2="{right+32}" y2="{by+22}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{left-32}" y1="{by+22}" x2="{right+32}" y2="{by+22}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """

# =========================================================
# TITLE BLOCK
# =========================================================
def title_block_svg(x, y, w, h, project_name, room_code, L_mm, W_mm, H_mm, wall_mm, ceil_mm, floor_mm, date_str, colors=None):
    c = colors or get_colors()
    return f"""
    <g>
        <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{c['line']}" stroke-width="1.1"/>
        <line x1="{x}" y1="{y+26}" x2="{x+w}" y2="{y+26}" stroke="{c['line']}" stroke-width="1"/>
        <line x1="{x+250}" y1="{y}" x2="{x+250}" y2="{y+h}" stroke="{c['line']}" stroke-width="1"/>
        <line x1="{x+420}" y1="{y}" x2="{x+420}" y2="{y+h}" stroke="{c['line']}" stroke-width="1"/>
        <line x1="{x}" y1="{y+58}" x2="{x+w}" y2="{y+58}" stroke="{c['line']}" stroke-width="1"/>

        {svg_text(x+12, y+18, "ECOPROM TECHNICAL DRAWING", size=12, anchor="start", weight="700", color=c["text"])}

        {svg_text(x+10, y+44, "Loyiha:", size=10, anchor="start", color=c["muted"])}
        {svg_text(x+70, y+44, project_name or "-", size=10, anchor="start", weight="700", color=c["text"])}

        {svg_text(x+260, y+44, "Kod:", size=10, anchor="start", color=c["muted"])}
        {svg_text(x+295, y+44, room_code, size=10, anchor="start", weight="700", color=c["text"])}

        {svg_text(x+430, y+44, "Sana:", size=10, anchor="start", color=c["muted"])}
        {svg_text(x+470, y+44, date_str, size=10, anchor="start", weight="700", color=c["text"])}

        {svg_text(x+10, y+76, f"O'lcham: {L_mm} x {W_mm} x {H_mm} mm", size=10, anchor="start", color=c["text"])}
        {svg_text(x+260, y+76, f"Devor: {wall_mm} mm", size=10, anchor="start", color=c["text"])}
        {svg_text(x+430, y+76, f"Patalok: {ceil_mm} mm", size=10, anchor="start", color=c["text"])}

        {svg_text(x+10, y+96, f"Pol: {floor_mm} mm", size=10, anchor="start", color=c["text"])}
        {svg_text(x+w-10, y+96, "Sheet: 1/1", size=10, anchor="end", color=c["muted"])}
    </g>
    """

# =========================================================
# MASTER TECHNICAL SHEET
# =========================================================
def make_technical_sheet_svg(
    L, W, H,
    wall_mm, ceil_mm, floor_mm,
    pol_bor,
    project_name,
    room_code,
    eshik_joyi="Chap",
    eshik="Muzlatkich eshigi",
    eshik_pozitsiya="O'rta",
    eshik_ochilish="Ichkariga"
):
    c = get_colors()

    outer_w_mm = m_to_mm(L)
    outer_h_mm = m_to_mm(W)
    outer_z_mm = m_to_mm(H)

    top_parts = build_side_segments(outer_w_mm, corner_mm=480, module_mm=960)
    right_parts = build_side_segments(outer_h_mm, corner_mm=480, module_mm=960)

    door_w_mm, door_h_mm = door_dimensions(eshik)

    top_meta = segment_meta(
        top_parts,
        has_door=(eshik != "Yo'q" and eshik_joyi in ["Old", "Orqa"]),
        door_size=door_w_mm
    )

    right_meta = segment_meta(
        right_parts,
        has_door=(eshik != "Yo'q" and eshik_joyi in ["Chap", "O'ng"]),
        door_size=door_w_mm
    )

    top_meta_plain = [{"size": p, "type": "panel"} for p in top_parts]
    right_meta_plain = [{"size": p, "type": "panel"} for p in right_parts]

    max_draw_w = 250
    max_draw_h = 185
    scale = min(max_draw_w / outer_w_mm, max_draw_h / outer_h_mm)

    draw_w = outer_w_mm * scale
    draw_h = outer_h_mm * scale
    wall_t = max(6, wall_mm * scale)

    svg_w = 794
    svg_h = 1123

    x_center = 390
    top_y = 120
    px = x_center - draw_w / 2
    py = top_y

    mid_y = 485
    bot_y = 760
    rx = x_center - draw_w / 2

    inner_L_mm = max(0, outer_w_mm - 2 * wall_mm)
    inner_W_mm = max(0, outer_h_mm - 2 * wall_mm)
    inner_H_mm = max(0, outer_z_mm - ceil_mm - (floor_mm if pol_bor else 0))

    inner_note_1 = svg_text(
        px + draw_w/2 + 8, py + draw_h/2 - 8, f"H-{outer_z_mm}",
        size=16, weight="700", rotate=90, color=c["text"]
    )
    inner_note_2 = svg_text(
        px + draw_w/2, py + draw_h + 45,
        f"Ichki: {inner_L_mm} x {inner_W_mm} x {inner_H_mm} mm",
        size=10, color=c["muted"]
    )

    door_note = ""
    door_shape = ""

    if eshik != "Yo'q":
        if eshik_joyi in ["Chap", "O'ng"]:
            door_offset_mm = get_door_offset_mm(
                right_parts,
                eshik_pozitsiya,
                side_type="vertical",
                door_size_mm=door_h_mm
            )
        else:
            door_offset_mm = get_door_offset_mm(
                top_parts,
                eshik_pozitsiya,
                side_type="horizontal",
                door_size_mm=door_w_mm
            )

        if eshik_joyi == "Chap":
            door_shape = draw_door_left(
                px, py, scale,
                door_offset_mm=door_offset_mm,
                door_h_mm=door_h_mm,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + 34,
                py + door_offset_mm * scale + (door_h_mm * scale) / 2,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=8,
                rotate=90,
                color=c["text"]
            )

        elif eshik_joyi == "O'ng":
            door_shape = draw_door_right(
                px, py, draw_w, scale,
                door_offset_mm=door_offset_mm,
                door_h_mm=door_h_mm,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + draw_w - 34,
                py + door_offset_mm * scale + (door_h_mm * scale) / 2,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=8,
                rotate=90,
                color=c["text"]
            )

        elif eshik_joyi == "Old":
            door_shape = draw_door_bottom(
                px, py, draw_h, scale,
                door_offset_mm=door_offset_mm,
                door_w_mm=door_w_mm,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + door_offset_mm * scale + (door_w_mm * scale) / 2,
                py + draw_h - 10,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=8,
                color=c["text"]
            )

        elif eshik_joyi == "Orqa":
            door_shape = draw_door_top(
                px, py, scale,
                door_offset_mm=door_offset_mm,
                door_w_mm=door_w_mm,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + door_offset_mm * scale + (door_w_mm * scale) / 2,
                py + 12,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=8,
                color=c["text"]
            )

    date_str = datetime.now().strftime("%d.%m.%Y")

    return f"""
    <svg width="100%" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="20" width="{svg_w-40}" height="{svg_h-40}" fill="{c['sheet']}" stroke="none"/>

        {svg_text(x_center, 60, "TEXNIK CHIZMA", size=14, weight="700", color=c["text"])}
        {svg_text(x_center, 82, (project_name or "").upper(), size=12, weight="700", color=c["text"])}
        {svg_text(710, 60, room_code, size=11, anchor="end", color=c["muted"])}

        {room_plan_svg(px, py, draw_w, draw_h, wall_t, c)}
        {door_shape}
        {door_note}
        {inner_note_1}
        {chain_dim_top(px, py-6, top_meta, scale, c["dim"])}
        {chain_dim_right(px+draw_w+8, py, right_meta, scale, c["dim"])}
        {draw_segment_ticks_top(px, py, top_meta, scale, c["line"])}
        {draw_segment_ticks_top(px, py+draw_h, top_meta, scale, c["line"])}
        {draw_segment_ticks_right(px, py, right_meta, scale, c["line"])}
        {draw_segment_ticks_right(px+draw_w, py, right_meta, scale, c["line"])}
        {svg_text(px + draw_w/2, py + draw_h + 24, f"Devor: {wall_mm} mm", size=11, color=c["text"])}
        {inner_note_2}

        {slab_svg(rx, mid_y, draw_w, draw_h, right_meta_plain, scale, "Patalok", c)}
        {chain_dim_top(rx, mid_y-6, top_meta_plain, scale, c["dim"])}
        {chain_dim_right(rx+draw_w+8, mid_y, right_meta_plain, scale, c["dim"])}
        {draw_segment_ticks_top(rx, mid_y, top_meta_plain, scale, c["line"])}
        {draw_segment_ticks_top(rx, mid_y+draw_h, top_meta_plain, scale, c["line"])}

        {slab_svg(rx, bot_y, draw_w, draw_h, right_meta_plain, scale, "Pol", c)}
        {chain_dim_top(rx, bot_y-6, top_meta_plain, scale, c["dim"])}
        {chain_dim_right(rx+draw_w+8, bot_y, right_meta_plain, scale, c["dim"])}
        {draw_segment_ticks_top(rx, bot_y, top_meta_plain, scale, c["line"])}
        {draw_segment_ticks_top(rx, bot_y+draw_h, top_meta_plain, scale, c["line"])}
        {svg_text(rx + draw_w/2, bot_y + draw_h + 24, f"Pol: {floor_mm if pol_bor else 0} mm", size=11, color=c["text"])}

        {title_block_svg(
            115, 980, 560, 110,
            project_name or "-", room_code,
            outer_w_mm, outer_h_mm, outer_z_mm,
            wall_mm, ceil_mm, floor_mm if pol_bor else 0,
            date_str, c
        )}

        {svg_text(714, 1088, "EcoProm", size=10, anchor="end", color=c["muted"])}
    </svg>
    """

# =========================================================
# 3D PLOTLY
# =========================================================
def add_box_mesh(fig, x, y, z, dx, dy, dz, color, name="", opacity=1.0, show_hover=True):
    xs = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    ys = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    zs = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]

    fig.add_trace(go.Mesh3d(
        x=xs,
        y=ys,
        z=zs,
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        color=color,
        opacity=opacity,
        flatshading=True,
        name=name,
        hoverinfo="text" if show_hover else "skip",
        text=name,
        showlegend=False
    ))

    fig.add_trace(go.Scatter3d(
        x=[x, x+dx, x+dx, x, x, x, x+dx, x+dx, x, x],
        y=[y, y, y+dy, y+dy, y, y, y, y+dy, y+dy, y],
        z=[z, z, z, z, z, z+dz, z+dz, z+dz, z+dz, z+dz],
        mode="lines",
        line=dict(color="#C9CED6", width=4),
        hoverinfo="skip",
        showlegend=False
    ))


def add_label(fig, x, y, z, text):
    fig.add_trace(go.Scatter3d(
        x=[x],
        y=[y],
        z=[z],
        mode="text",
        text=[text],
        textposition="middle center",
        hoverinfo="skip",
        showlegend=False
    ))


def add_panel_logo(fig, x, y, z, text="Eco Prom", color="#16A34A", size=10):
    fig.add_trace(go.Scatter3d(
        x=[x],
        y=[y],
        z=[z],
        mode="text",
        text=[text],
        textfont=dict(size=size, color=color),
        hoverinfo="skip",
        showlegend=False
    ))


def build_3d_figure(
    L, W, H,
    panel_type,
    thickness_mm,
    pol_bor,
    eshik,
    eshik_joyi,
    eshik_pozitsiya,
    agregat,
    agregat_joyi,
    ag_brand,
    progress_pct=100,
    show_labels=True
):
    palette = material_palette(panel_type)
    T = thickness_mm / 1000.0
    std_w = 0.96

    dw_mm, dh_mm = door_dimensions(eshik)
    dw = dw_mm / 1000.0
    dh = dh_mm / 1000.0

    def door_x_on_horizontal():
        if eshik_pozitsiya == "Chap":
            return 0.48
        elif eshik_pozitsiya == "O'ng":
            return max(0.0, L - 0.48 - dw)
        return max(0.0, (L - dw) / 2)

    def door_y_on_vertical():
        if eshik_pozitsiya == "Tepa":
            return 0.48
        elif eshik_pozitsiya == "Past":
            return max(0.0, W - 0.48 - dh)
        return max(0.0, (W - dh) / 2)

    all_elements = []

    # POL
    if pol_bor:
        cx = 0.0
        while cx < L - 1e-9:
            pw = min(std_w, L - cx)
            all_elements.append({
                "kind": "floor",
                "face": "top",
                "p": (cx, 0, -T),
                "d": (pw, W, T),
                "c": palette["floor"],
                "n": f"Pol paneli {pw:.2f}m"
            })
            cx += std_w

    # OLD DEVOR
    cx = 0.0
    door_x = door_x_on_horizontal() if eshik != "Yo'q" and eshik_joyi == "Old" else None
    while cx < L - 1e-9:
        pw = min(std_w, L - cx)
        if door_x is not None and cx <= door_x < cx + pw:
            left_gap = max(0.0, door_x - cx)
            right_gap = max(0.0, (cx + pw) - (door_x + dw))

            if left_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "front",
                    "p": (cx, 0, 0),
                    "d": (left_gap, T, H),
                    "c": palette["panel"],
                    "n": "Old devor"
                })
            if right_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "front",
                    "p": (door_x + dw, 0, 0),
                    "d": (right_gap, T, H),
                    "c": palette["panel"],
                    "n": "Old devor"
                })

            top_h = max(0.0, H - dh)
            if top_h > 0.02:
                all_elements.append({
                    "kind": "wall-top",
                    "face": "front",
                    "p": (door_x, 0, dh),
                    "d": (dw, T, top_h),
                    "c": palette["panel"],
                    "n": "Eshik usti panel"
                })
        else:
            all_elements.append({
                "kind": "wall",
                "face": "front",
                "p": (cx, 0, 0),
                "d": (pw, T, H),
                "c": palette["panel"],
                "n": "Old devor"
            })
        cx += std_w

    # ORQA DEVOR
    cx = 0.0
    door_x = door_x_on_horizontal() if eshik != "Yo'q" and eshik_joyi == "Orqa" else None
    while cx < L - 1e-9:
        pw = min(std_w, L - cx)
        if door_x is not None and cx <= door_x < cx + pw:
            left_gap = max(0.0, door_x - cx)
            right_gap = max(0.0, (cx + pw) - (door_x + dw))

            if left_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "back",
                    "p": (cx, W - T, 0),
                    "d": (left_gap, T, H),
                    "c": palette["panel"],
                    "n": "Orqa devor"
                })
            if right_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "back",
                    "p": (door_x + dw, W - T, 0),
                    "d": (right_gap, T, H),
                    "c": palette["panel"],
                    "n": "Orqa devor"
                })

            top_h = max(0.0, H - dh)
            if top_h > 0.02:
                all_elements.append({
                    "kind": "wall-top",
                    "face": "back",
                    "p": (door_x, W - T, dh),
                    "d": (dw, T, top_h),
                    "c": palette["panel"],
                    "n": "Eshik usti panel"
                })
        else:
            all_elements.append({
                "kind": "wall",
                "face": "back",
                "p": (cx, W - T, 0),
                "d": (pw, T, H),
                "c": palette["panel"],
                "n": "Orqa devor"
            })
        cx += std_w

    # CHAP DEVOR
    cy = T
    door_y = door_y_on_vertical() if eshik != "Yo'q" and eshik_joyi == "Chap" else None
    while cy < W - T - 1e-9:
        ph = min(std_w, (W - T) - cy)
        if door_y is not None and cy <= door_y < cy + ph:
            low_gap = max(0.0, door_y - cy)
            up_gap = max(0.0, (cy + ph) - (door_y + dh))

            if low_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "left",
                    "p": (0, cy, 0),
                    "d": (T, low_gap, H),
                    "c": palette["panel"],
                    "n": "Chap devor"
                })
            if up_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "left",
                    "p": (0, door_y + dh, 0),
                    "d": (T, up_gap, H),
                    "c": palette["panel"],
                    "n": "Chap devor"
                })

            top_h = max(0.0, H - dh)
            if top_h > 0.02:
                all_elements.append({
                    "kind": "wall-top",
                    "face": "left",
                    "p": (0, door_y, dh),
                    "d": (T, dh, top_h),
                    "c": palette["panel"],
                    "n": "Eshik usti panel"
                })
        else:
            all_elements.append({
                "kind": "wall",
                "face": "left",
                "p": (0, cy, 0),
                "d": (T, ph, H),
                "c": palette["panel"],
                "n": "Chap devor"
            })
        cy += std_w

    # O'NG DEVOR
    cy = T
    door_y = door_y_on_vertical() if eshik != "Yo'q" and eshik_joyi == "O'ng" else None
    while cy < W - T - 1e-9:
        ph = min(std_w, (W - T) - cy)
        if door_y is not None and cy <= door_y < cy + ph:
            low_gap = max(0.0, door_y - cy)
            up_gap = max(0.0, (cy + ph) - (door_y + dh))

            if low_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "right",
                    "p": (L - T, cy, 0),
                    "d": (T, low_gap, H),
                    "c": palette["panel"],
                    "n": "O'ng devor"
                })
            if up_gap > 0.02:
                all_elements.append({
                    "kind": "wall",
                    "face": "right",
                    "p": (L - T, door_y + dh, 0),
                    "d": (T, up_gap, H),
                    "c": palette["panel"],
                    "n": "O'ng devor"
                })

            top_h = max(0.0, H - dh)
            if top_h > 0.02:
                all_elements.append({
                    "kind": "wall-top",
                    "face": "right",
                    "p": (L - T, door_y, dh),
                    "d": (T, dh, top_h),
                    "c": palette["panel"],
                    "n": "Eshik usti panel"
                })
        else:
            all_elements.append({
                "kind": "wall",
                "face": "right",
                "p": (L - T, cy, 0),
                "d": (T, ph, H),
                "c": palette["panel"],
                "n": "O'ng devor"
            })
        cy += std_w

    # PATALOK
    cx = 0.0
    while cx < L - 1e-9:
        pw = min(std_w, L - cx)
        all_elements.append({
            "kind": "ceiling",
            "face": "top",
            "p": (cx, 0, H),
            "d": (pw, W, T),
            "c": palette["panel"],
            "n": f"Patalok paneli {pw:.2f}m",
            "op": 0.55
        })
        cx += std_w

    # ESHIK
    if eshik != "Yo'q":
        if eshik_joyi == "Old":
            all_elements.append({
                "kind": "door",
                "face": "front",
                "p": (door_x_on_horizontal(), -0.04, 0),
                "d": (dw, 0.08, dh),
                "c": palette["door"],
                "n": f"Eshik {dw:.2f}x{dh:.2f}"
            })
        elif eshik_joyi == "Orqa":
            all_elements.append({
                "kind": "door",
                "face": "back",
                "p": (door_x_on_horizontal(), W - 0.04, 0),
                "d": (dw, 0.08, dh),
                "c": palette["door"],
                "n": f"Eshik {dw:.2f}x{dh:.2f}"
            })
        elif eshik_joyi == "Chap":
            all_elements.append({
                "kind": "door",
                "face": "left",
                "p": (-0.04, door_y_on_vertical(), 0),
                "d": (0.08, dh, dh),
                "c": palette["door"],
                "n": f"Eshik {dw:.2f}x{dh:.2f}"
            })
        elif eshik_joyi == "O'ng":
            all_elements.append({
                "kind": "door",
                "face": "right",
                "p": (L - 0.04, door_y_on_vertical(), 0),
                "d": (0.08, dh, dh),
                "c": palette["door"],
                "n": f"Eshik {dw:.2f}x{dh:.2f}"
            })

    # AGREGAT
    if agregat != "Yo'q":
        ag_dx, ag_dy, ag_dz = 0.7, 0.6, 0.6
        if agregat_joyi == "Old":
            ag_pos = (max(0.0, L - 0.9), W / 2 - 0.3, max(0.0, H - 0.8))
        elif agregat_joyi == "Orqa":
            ag_pos = (0.2, W / 2 - 0.3, max(0.0, H - 0.8))
        elif agregat_joyi == "Chap":
            ag_pos = (0.1, max(0.0, W - 0.8), max(0.0, H - 0.8))
        else:
            ag_pos = (max(0.0, L - 0.8), 0.1, max(0.0, H - 0.8))

        all_elements.append({
            "kind": "aggr",
            "face": agregat_joyi.lower(),
            "p": ag_pos,
            "d": (ag_dx, ag_dy, ag_dz),
            "c": palette["aggr"],
            "n": f"Agregat: {ag_brand}"
        })

    visible_n = int(len(all_elements) * (progress_pct / 100.0))
    visible_n = max(0, min(len(all_elements), visible_n))

    fig = go.Figure()
    for i in range(visible_n):
        el = all_elements[i]
        x, y, z = el["p"]
        dx, dy, dz = el["d"]

        add_box_mesh(
            fig, x, y, z, dx, dy, dz,
            color=el["c"],
            name=el["n"],
            opacity=el.get("op", 1.0),
            show_hover=True
        )

        if show_labels:
            add_label(fig, x + dx / 2, y + dy / 2, z + dz / 2, el["kind"])

        if el["kind"] in ["wall", "wall-top", "ceiling", "floor"]:
            fx = x + dx / 2
            fy = y + dy / 2
            fz = z + dz / 2
            face = el.get("face", "")

            if face == "front":
                fy = y - 0.02
            elif face == "back":
                fy = y + dy + 0.02
            elif face == "left":
                fx = x - 0.02
            elif face == "right":
                fx = x + dx + 0.02
            elif face == "top":
                fz = z + dz / 2

            add_panel_logo(
                fig, fx, fy, fz,
                text="Eco Prom",
                color=palette["logo"],
                size=10
            )

    fig.update_layout(
        scene=dict(
            aspectmode="data",
            xaxis_title="Uzunlik (m)",
            yaxis_title="En (m)",
            zaxis_title="Balandlik (m)",
            bgcolor="rgba(0,0,0,0)",
            xaxis=dict(backgroundcolor="rgb(245,245,245)", gridcolor="#DDDDDD"),
            yaxis=dict(backgroundcolor="rgb(245,245,245)", gridcolor="#DDDDDD"),
            zaxis=dict(backgroundcolor="rgb(245,245,245)", gridcolor="#DDDDDD"),
        ),
        height=760,
        margin=dict(l=0, r=0, b=0, t=20)
    )
    return fig, len(all_elements), visible_n

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## ⚙️ EcoProm Control Panel")

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### 📏 O'lchamlar")
    st.text_input("Uzunlik (metr)", key="L_text", on_change=save_form_data)
    st.text_input("Eni (metr)", key="W_text", on_change=save_form_data)
    st.text_input("Balandlik (metr)", key="H_text", on_change=save_form_data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### 🧱 Panel va material")
    st.selectbox("Devor paneli turi", d_turi_options, key="d_turi", on_change=save_form_data)
    st.selectbox("Devor qalinligi", d_qalin_options, key="d_qalin", on_change=save_form_data)
    st.selectbox("Patalok turi", p_turi_options, key="p_turi", on_change=save_form_data)
    st.selectbox("Patalok qalinligi", p_qalin_options, key="p_qalin", on_change=save_form_data)
    st.selectbox("Panel ishchi eni", panel_width_options, key="panel_width_m", on_change=save_form_data)
    st.toggle("Pol paneli qo'shish", key="pol_bor", on_change=save_form_data)
    if st.session_state["pol_bor"]:
        st.selectbox("Pol turi", pol_turi_options, key="pol_turi", on_change=save_form_data)
        st.selectbox("Pol qalinligi", pol_qalin_options, key="pol_qalin", on_change=save_form_data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### 🚪 Eshik va agregat")
    st.selectbox("Eshik turi", eshik_options, key="eshik", on_change=save_form_data)
    st.radio("Eshik joyi", eshik_joyi_options, key="eshik_joyi", horizontal=False, on_change=save_form_data)

    current_pos_options = eshik_side_position_options if st.session_state["eshik_joyi"] in ["Chap", "O'ng"] else eshik_topbottom_position_options
    if st.session_state.get("eshik_pozitsiya") not in current_pos_options:
        st.session_state["eshik_pozitsiya"] = "O'rta"

    st.radio("Eshik pozitsiyasi", current_pos_options, key="eshik_pozitsiya", horizontal=False, on_change=save_form_data)
    st.radio("Eshik ochilishi", eshik_ochilish_options, key="eshik_ochilish", horizontal=False, on_change=save_form_data)

    st.selectbox("Agregat turi", agregat_options, key="agregat", on_change=save_form_data)
    st.radio("Agregat joylashuvi", agregat_joyi_options, key="agregat_joyi", horizontal=False, on_change=save_form_data)
    st.selectbox("Agregat brendi", ag_brand_options, key="ag_brand", on_change=save_form_data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### 🏗 3D sozlama")
    st.slider("Montaj jarayoni (%)", 0, 100, key="montaj_progress", on_change=save_form_data)
    st.toggle("3D label ko'rsatish", key="show_3d_labels", on_change=save_form_data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    st.markdown("### 📁 Loyiha")
    st.text_input("Loyiha nomi", key="project_name", on_change=save_form_data)
    st.text_input("Loyiha kodi", key="room_code", on_change=save_form_data)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# INPUT VALUES
# =========================================================
L = parse_dim(st.session_state["L_text"])
W = parse_dim(st.session_state["W_text"])
H = parse_dim(st.session_state["H_text"])

if not all(v is not None for v in [L, W, H]):
    st.title("🏗 EcoProm Professional Sovutish Kameralari Konstruktori")
    st.warning("Avval sidebar orqali uzunlik, eni va balandlikni to'g'ri kiriting.")
    st.stop()

d_turi = st.session_state["d_turi"]
d_qalin = st.session_state["d_qalin"]
p_turi = st.session_state["p_turi"]
p_qalin = st.session_state["p_qalin"]
panel_width_m = float(st.session_state["panel_width_m"])
pol_bor = st.session_state["pol_bor"]
pol_turi = st.session_state.get("pol_turi", "Mavjud emas") if pol_bor else "Mavjud emas"
pol_qalin = st.session_state.get("pol_qalin", "0mm") if pol_bor else "0mm"
eshik = st.session_state["eshik"]
eshik_joyi = st.session_state["eshik_joyi"]
eshik_pozitsiya = st.session_state["eshik_pozitsiya"]
eshik_ochilish = st.session_state["eshik_ochilish"]
agregat = st.session_state["agregat"]
agregat_joyi = st.session_state["agregat_joyi"]
project_name = st.session_state["project_name"]
room_code = st.session_state["room_code"]
ag_brand = st.session_state["ag_brand"]
montaj_progress = st.session_state["montaj_progress"]
show_3d_labels = st.session_state["show_3d_labels"]

# =========================================================
# TOP HEADER
# =========================================================
st.title("🏗 EcoProm Professional Constructor vNext")
st.write("Texnik chizma, 3D montaj vizualizatsiya, AI tavsiya va Telegram yuborishni bir joyga jamlagan professional konstruktor.")

palette = material_palette(d_turi)

st.markdown(
    f"""
    <span class="badge">Material: {d_turi}</span>
    <span class="badge">Devor qalinligi: {d_qalin}</span>
    <span class="badge">Patalok qalinligi: {p_qalin}</span>
    <span class="badge">Panel eni: {panel_width_m:.2f} m</span>
    <span class="badge">Montaj: {montaj_progress}%</span>
    """,
    unsafe_allow_html=True
)

# =========================================================
# AI ASSIST INPUTS
# =========================================================
st.divider()
st.subheader("1. AI Texnik Tavsiya")

ai1, ai2, ai3, ai4, ai5 = st.columns(5)

with ai1:
    mahsulot_turi = st.selectbox("Mahsulot turi", mahsulot_options, key="mahsulot_turi", on_change=save_form_data)
with ai2:
    saqlash_temp = st.text_input("Harorat", key="saqlash_temp", on_change=save_form_data)
with ai3:
    ochilish_soni = st.selectbox("Ochilish soni", ochilish_options, key="ochilish_soni", on_change=save_form_data)
with ai4:
    hudud = st.selectbox("Hudud", hudud_options, key="hudud", on_change=save_form_data)
with ai5:
    namlik_talabi = st.selectbox("Namlik", namlik_options, key="namlik_talabi", on_change=save_form_data)

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

a1, a2 = st.columns([1, 2])
with a1:
    if st.button("🤖 AI TAVSIYA OLISH"):
        with st.spinner("AI texnik tavsiya tayyorlamoqda..."):
            result = get_groq_recommendation(
                mahsulot_turi=mahsulot_turi,
                saqlash_temp=saqlash_temp,
                ochilish_soni=ochilish_soni,
                hudud=hudud,
                namlik_talabi=namlik_talabi,
                L=L,
                W=W,
                H=H,
                pol_bor=pol_bor
            )
            st.session_state.ai_result = result

with a2:
    if st.session_state.ai_result:
        ai_res = st.session_state.ai_result
        if ai_res.get("success"):
            d = ai_res["data"]
            st.markdown(f"""
            <div class="ai-box">
                <h3>🤖 AI Tavsiya</h3>
                <p><b>Rejim:</b> {d.get("rejim", "-")}</p>
                <p><b>Devor qalinligi:</b> {d.get("devor_qalinligi_mm", "-")} mm</p>
                <p><b>Patalok qalinligi:</b> {d.get("patalok_qalinligi_mm", "-")} mm</p>
                <p><b>Pol qalinligi:</b> {d.get("pol_qalinligi_mm", "-")} mm</p>
                <p><b>Agregat turi:</b> {d.get("agregat_turi", "-")}</p>
                <p><b>Eshik turi:</b> {d.get("eshik_turi", "-")}</p>
                <p><b>Izoh:</b> {d.get("izoh", "-")}</p>
                <p><b>Xulosa:</b> {d.get("xulosa", "-")}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(ai_res.get("message", "Noma'lum xato"))

# =========================================================
# CALCULATIONS
# =========================================================
wall_mm = mm_val(d_qalin)
ceil_mm = mm_val(p_qalin)
floor_mm = mm_val(pol_qalin) if pol_bor else 0
door_w_mm, door_h_mm = door_dimensions(eshik)

hajm = round(L * W * H, 2)
inner_hajm = round(
    max(0, (m_to_mm(L) - 2 * wall_mm) / 1000) *
    max(0, (m_to_mm(W) - 2 * wall_mm) / 1000) *
    max(0, (m_to_mm(H) - ceil_mm - floor_mm) / 1000),
    2
)

s_devor = round(2 * (L + W) * H, 2)
s_patalok = round(L * W, 2)
s_pol = round(L * W, 2) if pol_bor else 0
total_panel_area = round(s_devor + s_patalok + s_pol, 2)

inner_L_mm = max(0, m_to_mm(L) - (2 * wall_mm))
inner_W_mm = max(0, m_to_mm(W) - (2 * wall_mm))
inner_H_mm = max(0, m_to_mm(H) - ceil_mm - (floor_mm if pol_bor else 0))

wall_layout_L = panel_count_linear(L, panel_width_m)
wall_layout_W = panel_count_linear(W, panel_width_m)

devor_panels_total = (wall_layout_L["total_panels"] * 2) + (wall_layout_W["total_panels"] * 2)
patalok_panels_total = math.ceil(W / panel_width_m)
pol_panels_total = math.ceil(W / panel_width_m) if pol_bor else 0
estimated_all_panels = devor_panels_total + patalok_panels_total + pol_panels_total

top_parts = build_side_segments(m_to_mm(L), corner_mm=480, module_mm=960)
right_parts = build_side_segments(m_to_mm(W), corner_mm=480, module_mm=960)

top_meta = segment_meta(
    top_parts,
    has_door=(eshik != "Yo'q" and eshik_joyi in ["Old", "Orqa"]),
    door_size=door_w_mm
)

right_meta = segment_meta(
    right_parts,
    has_door=(eshik != "Yo'q" and eshik_joyi in ["Chap", "O'ng"]),
    door_size=door_w_mm
)

# =========================================================
# METRICS
# =========================================================
st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Tashqi hajm</div><div class="metric-value">{hajm} m³</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Ichki foydali hajm</div><div class="metric-value">{inner_hajm} m³</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Devor maydoni</div><div class="metric-value">{s_devor} m²</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Jami panel maydoni</div><div class="metric-value">{total_panel_area} m²</div></div>', unsafe_allow_html=True)
with m5:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Taxminiy panel soni</div><div class="metric-value">{estimated_all_panels} ta</div></div>', unsafe_allow_html=True)

# =========================================================
# MAIN VIEW: 3D + SPEC
# =========================================================
st.divider()
st.subheader("2. 3D Vizualizatsiya va Spetsifikatsiya")

fig_3d, total_elements, visible_elements = build_3d_figure(
    L=L,
    W=W,
    H=H,
    panel_type=d_turi,
    thickness_mm=wall_mm,
    pol_bor=pol_bor,
    eshik=eshik,
    eshik_joyi=eshik_joyi,
    eshik_pozitsiya=eshik_pozitsiya,
    agregat=agregat,
    agregat_joyi=agregat_joyi,
    ag_brand=ag_brand,
    progress_pct=montaj_progress,
    show_labels=show_3d_labels
)

left, right = st.columns([3.2, 1.3])

with left:
    st.plotly_chart(fig_3d, use_container_width=True)

with right:
    st.markdown("<div class='spec-card'>", unsafe_allow_html=True)
    st.markdown("### 📝 Spetsifikatsiya")
    st.info(f"Material: {d_turi}")
    st.info(f"Eshik: {eshik}")
    st.info(f"Agregat: {ag_brand if agregat != "Yo'q" else 'Yo‘q'}")
    st.info(f"Montaj ko‘rinishi: {visible_elements}/{total_elements} element")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='spec-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 Hisob-kitob")
    st.success(f"Tashqi o'lcham: {L:.2f} × {W:.2f} × {H:.2f} m")
    st.success(f"Ichki o'lcham: {inner_L_mm} × {inner_W_mm} × {inner_H_mm} mm")
    st.success(f"Panel yuzasi: {total_panel_area} m²")
    st.success(f"Ichki hajm: {inner_hajm} m³")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='spec-card'>", unsafe_allow_html=True)
    st.markdown("### 🧩 Komplekt")
    st.write(f"**Devor paneli:** {devor_panels_total} ta")
    st.write(f"**Patalok paneli:** {patalok_panels_total} ta")
    st.write(f"**Pol paneli:** {pol_panels_total if pol_bor else 0} ta")
    st.write(f"**Eshik:** {eshik}")
    st.write(f"**Agregat:** {agregat}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# TECH DRAWING
# =========================================================
st.divider()
st.subheader("3. Texnik Chizma Listi")

sheet_svg = make_technical_sheet_svg(
    L=L,
    W=W,
    H=H,
    wall_mm=wall_mm,
    ceil_mm=ceil_mm,
    floor_mm=floor_mm,
    pol_bor=pol_bor,
    project_name=project_name,
    room_code=room_code,
    eshik_joyi=eshik_joyi,
    eshik=eshik,
    eshik_pozitsiya=eshik_pozitsiya,
    eshik_ochilish=eshik_ochilish
)

draw_svg(sheet_svg, height=1080)
st.caption("Texnik listda har bir tomonda burchak 480 mm, markaziy qism 960 mm modul bo‘yicha ajratilgan. Eshik aniq joylashuvi reja ichida ko‘rsatilgan.")

# =========================================================
# SPEC TABLES
# =========================================================
st.divider()
st.subheader("4. Panel раскладка va Texnik Tafsilot")

t1, t2, t3 = st.columns(3)

with t1:
    st.markdown("<div class='tech-table'>", unsafe_allow_html=True)
    st.markdown("### Devor segmentatsiyasi")
    top_label = " + ".join([f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in top_meta])
    right_label = " + ".join([f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in right_meta])

    st.write(f"**Uzunlik tomoni ({fmt_mm(m_to_mm(L))}):** {top_label}")
    st.write(f"**En tomoni ({fmt_mm(m_to_mm(W))}):** {right_label}")
    st.write("**Burchak moduli:** 480 mm")
    st.write("**Asosiy modul:** 960 mm")
    if eshik != "Yo'q":
        st.write(f"**Eshik moduli:** {door_w_mm} mm ({eshik_joyi}, {eshik_pozitsiya})")
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    st.markdown("<div class='tech-table'>", unsafe_allow_html=True)
    st.markdown("### Panel раскладка")
    st.write(f"**Uzun devor (2 ta):** {L:.2f} m")
    st.write(f"- To'liq panel: {wall_layout_L['full_panels']} ta")
    st.write(f"- Qoldiq panel: {wall_layout_L['remainder_m']:.3f} m")

    st.write(f"**Qisqa devor (2 ta):** {W:.2f} m")
    st.write(f"- To'liq panel: {wall_layout_W['full_panels']} ta")
    st.write(f"- Qoldiq panel: {wall_layout_W['remainder_m']:.3f} m")

    st.write(f"**Umumiy devor paneli:** {devor_panels_total} ta")
    st.write(f"**Patalok paneli:** {patalok_panels_total} ta")
    st.write(f"**Pol paneli:** {pol_panels_total if pol_bor else 0} ta")
    st.markdown("</div>", unsafe_allow_html=True)

with t3:
    st.markdown("<div class='tech-table'>", unsafe_allow_html=True)
    st.markdown("### Texnik xulosa")
    st.write(f"**Devor:** {d_turi} / {wall_mm} mm")
    st.write(f"**Patalok:** {p_turi} / {ceil_mm} mm")
    st.write(f"**Pol:** {pol_turi if pol_bor else 'Mavjud emas'} / {floor_mm if pol_bor else 0} mm")
    st.write(f"**Eshik:** {eshik}")
    st.write(f"**Eshik ochilishi:** {eshik_ochilish}")
    st.write(f"**Agregat:** {agregat}")
    st.write(f"**Brend:** {ag_brand if agregat != "Yoq" else 'Mavjud emas'}")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# SAVE / RESET
# =========================================================
st.divider()
c_save, c_reset = st.columns(2)

with c_save:
    if st.button("💾 MA'LUMOTNI SAQLASH"):
        save_form_data()
        st.success("Ma'lumot saqlandi")

with c_reset:
    if st.button("🗑 TOZALASH"):
        if DATA_FILE.exists():
            DATA_FILE.unlink()

        for k in list(st.session_state.keys()):
            del st.session_state[k]

        for k, v in DEFAULT_FORM_DATA.items():
            st.session_state[k] = v

        st.session_state.ai_result = None
        st.rerun()

# =========================================================
# EXPORTABLE JSON
# =========================================================
st.divider()
export_payload = {
    "project_name": project_name,
    "room_code": room_code,
    "dimensions_m": {"L": L, "W": W, "H": H},
    "dimensions_inner_mm": {
        "L": inner_L_mm,
        "W": inner_W_mm,
        "H": inner_H_mm
    },
    "material": {
        "wall_type": d_turi,
        "wall_mm": wall_mm,
        "ceiling_type": p_turi,
        "ceiling_mm": ceil_mm,
        "floor_type": pol_turi if pol_bor else "Mavjud emas",
        "floor_mm": floor_mm if pol_bor else 0,
        "panel_width_m": panel_width_m
    },
    "door": {
        "type": eshik,
        "position_side": eshik_joyi,
        "position": eshik_pozitsiya,
        "opening": eshik_ochilish,
        "width_mm": door_w_mm,
        "height_mm": door_h_mm
    },
    "agregat": {
        "type": agregat,
        "position": agregat_joyi,
        "brand": ag_brand
    },
    "calculations": {
        "outer_volume_m3": hajm,
        "inner_volume_m3": inner_hajm,
        "wall_area_m2": s_devor,
        "ceiling_area_m2": s_patalok,
        "floor_area_m2": s_pol,
        "total_panel_area_m2": total_panel_area,
        "wall_panels_total": devor_panels_total,
        "ceiling_panels_total": patalok_panels_total,
        "floor_panels_total": pol_panels_total,
    },
    "segments": {
        "top_meta": top_meta,
        "right_meta": right_meta
    },
    "ai_result": st.session_state.ai_result["data"] if st.session_state.ai_result and st.session_state.ai_result.get("success") else None,
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

json_str = json.dumps(export_payload, indent=2, ensure_ascii=False)

d1, d2 = st.columns(2)
with d1:
    st.download_button(
        "⬇️ JSON YUKLAB OLISH",
        data=json_str.encode("utf-8"),
        file_name=f"{room_code or 'ecoprom'}_report.json",
        mime="application/json"
    )
with d2:
    st.download_button(
        "⬇️ SVG CHIZMANI YUKLAB OLISH",
        data=sheet_svg.encode("utf-8"),
        file_name=f"{room_code or 'ecoprom'}_technical_sheet.svg",
        mime="image/svg+xml"
    )

# =========================================================
# FINAL REPORT + TELEGRAM
# =========================================================
st.divider()
if st.button("📨 HISOBLASH VA ADMINGA YUBORISH"):
    ai_data = None
    ai_summary = ""

    if st.session_state.ai_result and st.session_state.ai_result.get("success"):
        ai_data = st.session_state.ai_result["data"]
        ai_summary = f"""
        <hr>
        <h4>🤖 AI Tavsiya Xulosasi</h4>
        <p><b>Rejim:</b> {ai_data.get("rejim", "-")}</p>
        <p><b>AI devor qalinligi:</b> {ai_data.get("devor_qalinligi_mm", "-")} mm</p>
        <p><b>AI patalok qalinligi:</b> {ai_data.get("patalok_qalinligi_mm", "-")} mm</p>
        <p><b>AI pol qalinligi:</b> {ai_data.get("pol_qalinligi_mm", "-")} mm</p>
        <p><b>AI agregat turi:</b> {ai_data.get("agregat_turi", "-")}</p>
        <p><b>AI eshik turi:</b> {ai_data.get("eshik_turi", "-")}</p>
        <p><b>AI izoh:</b> {ai_data.get("izoh", "-")}</p>
        <p><b>AI xulosa:</b> {ai_data.get("xulosa", "-")}</p>
        """

    top_report = " + ".join(
        [f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in top_meta]
    )
    right_report = " + ".join(
        [f"{p['size']} ESHIK" if p["type"] == "door" else str(p["size"]) for p in right_meta]
    )

    report_payload = {
        "project_name": project_name,
        "room_code": room_code,
        "L": L,
        "W": W,
        "H": H,
        "inner_L_mm": inner_L_mm,
        "inner_W_mm": inner_W_mm,
        "inner_H_mm": inner_H_mm,
        "hajm": hajm,
        "d_turi": d_turi,
        "wall_mm": wall_mm,
        "s_devor": s_devor,
        "p_turi": p_turi,
        "ceil_mm": ceil_mm,
        "s_patalok": s_patalok,
        "pol_turi": pol_turi,
        "pol_bor": pol_bor,
        "floor_mm": floor_mm,
        "s_pol": s_pol,
        "eshik": eshik,
        "eshik_joyi": eshik_joyi,
        "eshik_pozitsiya": eshik_pozitsiya,
        "eshik_ochilish": eshik_ochilish,
        "agregat": agregat,
        "agregat_joyi": agregat_joyi,
        "panel_width_m": panel_width_m,
        "devor_panels_total": devor_panels_total,
        "patalok_panels_total": patalok_panels_total,
        "pol_panels_total": pol_panels_total,
        "mahsulot_turi": mahsulot_turi,
        "saqlash_temp": saqlash_temp,
        "ochilish_soni": ochilish_soni,
        "hudud": hudud,
        "namlik_talabi": namlik_talabi,
        "top_meta": top_meta,
        "right_meta": right_meta,
        "ai_data": ai_data,
    }

    telegram_message = build_telegram_message(report_payload)
    tg_ok, tg_msg = send_to_telegram_channel(telegram_message)

    st.markdown(f"""
    <div class="report-box">
        <h3>📄 Buyurtma Tafsilotlari</h3>

        <p><b>Loyiha:</b> {project_name or "-"}</p>
        <p><b>Kod:</b> {room_code}</p>
        <hr>

        <p><b>Tashqi o'lcham:</b> {fmt_m(L)} × {fmt_m(W)} × {fmt_m(H)}</p>
        <p><b>Ichki foydali o'lcham:</b> {inner_L_mm} × {inner_W_mm} × {inner_H_mm} mm</p>
        <p><b>Tashqi hajm:</b> {hajm} m³</p>
        <p><b>Ichki foydali hajm:</b> {inner_hajm} m³</p>

        <hr>

        <p><b>Devor:</b> {d_turi} / {wall_mm} mm — {s_devor} m²</p>
        <p><b>Patalok:</b> {p_turi} / {ceil_mm} mm — {s_patalok} m²</p>
        <p><b>Pol:</b> {pol_turi if pol_bor else "Mavjud emas"} {" / " + str(floor_mm) + " mm" if pol_bor else ""} — {s_pol} m²</p>
        <p><b>Jami panel yuzasi:</b> {total_panel_area} m²</p>

        <hr>

        <p><b>Eshik:</b> {eshik} {f"({door_w_mm}x{door_h_mm} mm)" if eshik != "Yo'q" else ""}</p>
        <p><b>Eshik joylashuvi:</b> {eshik_joyi}</p>
        <p><b>Eshik pozitsiyasi:</b> {eshik_pozitsiya if eshik != "Yo'q" else "Mavjud emas"}</p>
        <p><b>Eshik ochilishi:</b> {eshik_ochilish}</p>

        <p><b>Agregat:</b> {agregat}</p>
        <p><b>Agregat joylashuvi:</b> {agregat_joyi if agregat != "Yo'q" else "Mavjud emas"}</p>
        <p><b>Agregat brendi:</b> {ag_brand if agregat != "Yo'q" else "Mavjud emas"}</p>

        <hr>

        <p><b>Uzunlik tomoni segmentlari:</b> {top_report}</p>
        <p><b>En tomoni segmentlari:</b> {right_report}</p>

        <p><b>Panel ishchi eni:</b> {panel_width_m:.2f} m</p>
        <p><b>Umumiy devor panel soni:</b> {devor_panels_total} ta</p>
        <p><b>Taxminiy patalok panel soni:</b> {patalok_panels_total} ta</p>
        <p><b>Taxminiy pol panel soni:</b> {pol_panels_total if pol_bor else 0} ta</p>
        <p><b>Jami taxminiy panel soni:</b> {estimated_all_panels} ta</p>

        {ai_summary}

        <hr>

        <p><b>Montaj progress preview:</b> {montaj_progress}%</p>
        <p><b>Texnik izoh:</b> Har bir tomonda burchak 480 mm, markaziy qism 960 mm modul bo'yicha ajratildi. Eshik o'z segmenti ichida aniq ko'rsatildi. Ichki foydali o'lchamlar va 3D montaj preview qo'shildi.</p>
    </div>
    """, unsafe_allow_html=True)

    if tg_ok:
        st.success("Ma'lumot Telegram kanalga yuborildi.")
    else:
        st.error(f"Telegramga yuborilmadi: {tg_msg}")

    save_form_data()
    st.toast("Ma'lumotlar tayyor. Saqlandi va yuborildi.")
