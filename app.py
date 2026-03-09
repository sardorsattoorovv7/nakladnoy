import os
import math
import json
import html
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

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
    "L_text": "",
    "W_text": "",
    "H_text": "",
    "d_turi": "Sovutgich (PIR)",
    "d_qalin": "100mm",
    "p_turi": "Sovutgich (PIR)",
    "p_qalin": "80mm",
    "panel_width_m": 1.16,
    "pol_bor": True,
    "pol_turi": "PIR (Standart)",
    "pol_qalin": "100mm",
    "eshik": "Muzlatkich eshigi",
    "eshik_joyi": "Chap",
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
}

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
.main {
    background: #e6e6e6;
}
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}
h1, h2, h3 {
    color: #111111;
}
.stButton > button {
    width: 100%;
    border-radius: 8px;
    height: 2.8em;
    background: #111111;
    color: white;
    font-weight: 600;
    border: none;
}
.report-box,
.metric-box,
.tech-table,
.ai-box {
    background: white;
    border-radius: 10px;
    border: 1px solid #d9d9d9;
    box-shadow: none;
}
.report-box {
    padding: 20px;
}
.metric-box {
    padding: 16px;
    text-align: center;
    min-height: 90px;
}
.metric-title {
    color: #555;
    font-size: 13px;
}
.metric-value {
    color: #111;
    font-size: 24px;
    font-weight: 700;
    margin-top: 8px;
}
.tech-table {
    padding: 18px;
    height: 100%;
}
.ai-box {
    padding: 18px;
    border-left: 6px solid #333;
}
hr {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}
small, .stCaption {
    color: #666 !important;
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
def mm_val(s: str) -> int:
    return int(str(s).replace("mm", "").strip())


def m_to_mm(m: float) -> int:
    return int(round(m * 1000))


def fmt_m(v: float) -> str:
    return f"{v:.2f} m"


def fmt_mm(v: int) -> str:
    return f"{int(v)} mm"


def draw_svg(svg_code: str, height: int = 1080):
    html_code = f"""
    <div style="width:100%; background:#dcdcdc; padding:16px; overflow:auto;">
        {svg_code}
    </div>
    """
    components.html(html_code, height=height, scrolling=True)


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

<b>Mahsulot turi:</b> {telegram_escape_html(data["mahsulot_turi"])}
<b>Harorat:</b> {telegram_escape_html(data["saqlash_temp"])}
<b>Ochilish soni:</b> {telegram_escape_html(data["ochilish_soni"])}
<b>Hudud:</b> {telegram_escape_html(data["hudud"])}
<b>Namlik:</b> {telegram_escape_html(data["namlik_talabi"])}
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


def draw_door_left(x, y, outer_h, scale, door_h_mm=2000, position="O'rta", opening="Ichkariga", colors=None):
    c = colors or get_colors()
    door_h = door_h_mm * scale
    margin = 18

    if position == "Tepa":
        top = y + margin
        bot = top + door_h
    elif position == "Past":
        bot = y + outer_h - margin
        top = bot - door_h
    else:
        mid = y + outer_h / 2
        top = mid - door_h / 2
        bot = mid + door_h / 2

    if opening == "Ichkariga":
        return f"""
        <line x1="{x}" y1="{top}" x2="{x+28}" y2="{top+46}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{x}" y1="{bot}" x2="{x+28}" y2="{bot-46}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{x+28}" y1="{top+46}" x2="{x+28}" y2="{bot-46}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{x}" y1="{top}" x2="{x-28}" y2="{top-46}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{x}" y1="{bot}" x2="{x-28}" y2="{bot+46}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{x-28}" y1="{top-46}" x2="{x-28}" y2="{bot+46}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_right(x, y, outer_w, outer_h, scale, door_h_mm=2000, position="O'rta", opening="Ichkariga", colors=None):
    c = colors or get_colors()
    door_h = door_h_mm * scale
    rx = x + outer_w
    margin = 18

    if position == "Tepa":
        top = y + margin
        bot = top + door_h
    elif position == "Past":
        bot = y + outer_h - margin
        top = bot - door_h
    else:
        mid = y + outer_h / 2
        top = mid - door_h / 2
        bot = mid + door_h / 2

    if opening == "Ichkariga":
        return f"""
        <line x1="{rx}" y1="{top}" x2="{rx-28}" y2="{top+46}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{rx}" y1="{bot}" x2="{rx-28}" y2="{bot-46}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{rx-28}" y1="{top+46}" x2="{rx-28}" y2="{bot-46}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{rx}" y1="{top}" x2="{rx+28}" y2="{top-46}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{rx}" y1="{bot}" x2="{rx+28}" y2="{bot+46}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{rx+28}" y1="{top-46}" x2="{rx+28}" y2="{bot+46}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_top(x, y, outer_w, scale, door_w_mm=960, position="O'rta", opening="Ichkariga", colors=None):
    c = colors or get_colors()
    door_w = door_w_mm * scale
    margin = 18

    if position == "Chap":
        left = x + margin
        right = left + door_w
    elif position == "O'ng":
        right = x + outer_w - margin
        left = right - door_w
    else:
        mid = x + outer_w / 2
        left = mid - door_w / 2
        right = mid + door_w / 2

    if opening == "Ichkariga":
        return f"""
        <line x1="{left}" y1="{y}" x2="{left+46}" y2="{y+28}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{right}" y1="{y}" x2="{right-46}" y2="{y+28}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{left+46}" y1="{y+28}" x2="{right-46}" y2="{y+28}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{left}" y1="{y}" x2="{left-46}" y2="{y-28}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{right}" y1="{y}" x2="{right+46}" y2="{y-28}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{left-46}" y1="{y-28}" x2="{right+46}" y2="{y-28}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
    """


def draw_door_bottom(x, y, outer_w, outer_h, scale, door_w_mm=960, position="O'rta", opening="Ichkariga", colors=None):
    c = colors or get_colors()
    door_w = door_w_mm * scale
    by = y + outer_h
    margin = 18

    if position == "Chap":
        left = x + margin
        right = left + door_w
    elif position == "O'ng":
        right = x + outer_w - margin
        left = right - door_w
    else:
        mid = x + outer_w / 2
        left = mid - door_w / 2
        right = mid + door_w / 2

    if opening == "Ichkariga":
        return f"""
        <line x1="{left}" y1="{by}" x2="{left+46}" y2="{by-28}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{right}" y1="{by}" x2="{right-46}" y2="{by-28}" stroke="{c["door"]}" stroke-width="1.4"/>
        <line x1="{left+46}" y1="{by-28}" x2="{right-46}" y2="{by-28}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
        """
    return f"""
    <line x1="{left}" y1="{by}" x2="{left-46}" y2="{by+28}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{right}" y1="{by}" x2="{right+46}" y2="{by+28}" stroke="{c["door"]}" stroke-width="1.4"/>
    <line x1="{left-46}" y1="{by+28}" x2="{right+46}" y2="{by+28}" stroke="{c["door"]}" stroke-width="1.4" stroke-dasharray="4,3"/>
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
        if eshik_joyi == "Chap":
            door_shape = draw_door_left(
                px, py, draw_h, scale,
                door_h_mm=door_h_mm,
                position=eshik_pozitsiya,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + 34, py + draw_h/2,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=9, rotate=90, color=c["text"]
            )

        elif eshik_joyi == "O'ng":
            door_shape = draw_door_right(
                px, py, draw_w, draw_h, scale,
                door_h_mm=door_h_mm,
                position=eshik_pozitsiya,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + draw_w - 34, py + draw_h/2,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=9, rotate=90, color=c["text"]
            )

        elif eshik_joyi == "Old":
            door_shape = draw_door_bottom(
                px, py, draw_w, draw_h, scale,
                door_w_mm=door_w_mm,
                position=eshik_pozitsiya,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + draw_w/2, py + draw_h - 10,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=9, color=c["text"]
            )

        elif eshik_joyi == "Orqa":
            door_shape = draw_door_top(
                px, py, draw_w, scale,
                door_w_mm=door_w_mm,
                position=eshik_pozitsiya,
                opening=eshik_ochilish,
                colors=c
            )
            door_note = svg_text(
                px + draw_w/2, py + 12,
                f"ESHIK {door_w_mm}x{door_h_mm} / {eshik_ochilish.upper()} / {eshik_pozitsiya.upper()}",
                size=9, color=c["text"]
            )

    date_str = datetime.now().strftime("%d.%m.%Y")

    return f"""
    <svg width="100%" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="20" width="{svg_w-40}" height="{svg_h-40}" fill="{c['sheet']}" stroke="none"/>

        {svg_text(x_center, 60, "TEXNIK CHIZMA", size=14, weight="700", color=c["text"])}
        {svg_text(x_center, 82, (project_name or "").upper(), size=12, weight="700", color=c["text"])}
        {svg_text(710, 60, room_code, size=11, anchor="end", color=c["muted"])}

        <!-- REJA -->
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

        <!-- PATALOK -->
        {slab_svg(rx, mid_y, draw_w, draw_h, right_meta_plain, scale, "Patalok", c)}
        {chain_dim_top(rx, mid_y-6, top_meta_plain, scale, c["dim"])}
        {chain_dim_right(rx+draw_w+8, mid_y, right_meta_plain, scale, c["dim"])}
        {draw_segment_ticks_top(rx, mid_y, top_meta_plain, scale, c["line"])}
        {draw_segment_ticks_top(rx, mid_y+draw_h, top_meta_plain, scale, c["line"])}

        <!-- POL -->
        {slab_svg(rx, bot_y, draw_w, draw_h, right_meta_plain, scale, "Pol", c)}
        {chain_dim_top(rx, bot_y-6, top_meta_plain, scale, c["dim"])}
        {chain_dim_right(rx+draw_w+8, bot_y, right_meta_plain, scale, c["dim"])}
        {draw_segment_ticks_top(rx, bot_y, top_meta_plain, scale, c["line"])}
        {draw_segment_ticks_top(rx, bot_y+draw_h, top_meta_plain, scale, c["line"])}
        {svg_text(rx + draw_w/2, bot_y + draw_h + 24, f"Pol: {floor_mm if pol_bor else 0} mm", size=11, color=c["text"])}

        <!-- TITLE BLOCK -->
        {title_block_svg(
            115, 980, 560, 110,
            project_name or "-", room_code,
            outer_w_mm, outer_h_mm, outer_z_mm,
            wall_mm, ceil_mm, floor_mm if pol_bor else 0,
            date_str, c
        )}

        <!-- FOOTER -->
        {svg_text(714, 1088, "EcoProm", size=10, anchor="end", color=c["muted"])}
    </svg>
    """

# =========================================================
# OPTIONS
# =========================================================
d_turi_options = ["Sovutgich (PIR)", "Oddiy Devor", "Sendvich Mineral paxta"]
d_qalin_options = ["50mm", "80mm", "100mm", "120mm", "150mm"]
p_turi_options = ["Sovutgich (PIR)", "Tom uchun (Trapsiya)", "Tekis panel"]
p_qalin_options = ["50mm", "80mm", "100mm", "120mm"]
panel_width_options = [1.00, 1.16]
pol_turi_options = ["PIR (Kuchaytirilgan)", "PIR (Standart)"]
pol_qalin_options = ["50mm", "80mm", "100mm", "120mm"]
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

# =========================================================
# HEADER
# =========================================================
st.title("🏗 EcoProm: Professional Sovutish Kameralari Konstruktori")
st.write("Mijoz o‘lchamlarini kiriting, AI tavsiya oling va PDF-uslubdagi professional texnik chizma hosil qiling.")

# =========================================================
# INPUTS
# =========================================================
st.subheader("1. Asosiy o'lchamlar")

c1, c2, c3 = st.columns(3)
L_text = c1.text_input("Uzunlik (metr)", key="L_text", placeholder="Masalan: 3.0", on_change=save_form_data)
W_text = c2.text_input("Eni (metr)", key="W_text", placeholder="Masalan: 2.5", on_change=save_form_data)
H_text = c3.text_input("Balandlik (metr)", key="H_text", placeholder="Masalan: 2.5", on_change=save_form_data)

L = parse_dim(L_text)
W = parse_dim(W_text)
H = parse_dim(H_text)

dims_ready = all(v is not None for v in [L, W, H])

if not dims_ready:
    st.warning("Avval uzunlik, eni va balandlikni kiriting. Refresh bo‘lsa ham ma’lumot saqlanadi.")
    st.stop()

st.divider()

st.subheader("2. Panel va Materiallar")
col_left, col_right = st.columns(2)

with col_left:
    st.info("📦 Devor va Patalok")

    d_turi = st.selectbox(
        "Devor paneli turi",
        d_turi_options,
        index=d_turi_options.index(st.session_state["d_turi"]),
        key="d_turi",
        on_change=save_form_data
    )

    d_qalin = st.selectbox(
        "Devor qalinligi",
        d_qalin_options,
        index=d_qalin_options.index(st.session_state["d_qalin"]),
        key="d_qalin",
        on_change=save_form_data
    )

    p_turi = st.selectbox(
        "Patalok paneli turi",
        p_turi_options,
        index=p_turi_options.index(st.session_state["p_turi"]),
        key="p_turi",
        on_change=save_form_data
    )

    p_qalin = st.selectbox(
        "Patalok qalinligi",
        p_qalin_options,
        index=p_qalin_options.index(st.session_state["p_qalin"]),
        key="p_qalin",
        on_change=save_form_data
    )

    panel_width_m = st.selectbox(
        "Panel ishchi eni",
        panel_width_options,
        index=panel_width_options.index(st.session_state["panel_width_m"]),
        key="panel_width_m",
        on_change=save_form_data
    )

with col_right:
    st.info("⚙️ Pol va Qo'shimchalar")

    pol_bor = st.toggle(
        "Pol paneli qo'shish",
        key="pol_bor",
        on_change=save_form_data
    )

    if pol_bor:
        pol_turi = st.selectbox(
            "Pol paneli turi",
            pol_turi_options,
            index=pol_turi_options.index(st.session_state["pol_turi"]),
            key="pol_turi",
            on_change=save_form_data
        )

        pol_qalin = st.selectbox(
            "Pol qalinligi",
            pol_qalin_options,
            index=pol_qalin_options.index(st.session_state["pol_qalin"]),
            key="pol_qalin",
            on_change=save_form_data
        )
    else:
        pol_turi = "Mavjud emas"
        pol_qalin = "0mm"

    eshik = st.selectbox(
        "Eshik tanlash",
        eshik_options,
        index=eshik_options.index(st.session_state["eshik"]),
        key="eshik",
        on_change=save_form_data
    )

    eshik_joyi = st.radio(
        "Eshik qayerda bo'lsin?",
        eshik_joyi_options,
        index=eshik_joyi_options.index(st.session_state["eshik_joyi"]),
        horizontal=True,
        key="eshik_joyi",
        on_change=save_form_data
    )

    if st.session_state["eshik_joyi"] in ["Chap", "O'ng"]:
        current_pos_options = eshik_side_position_options
    else:
        current_pos_options = eshik_topbottom_position_options

    if st.session_state.get("eshik_pozitsiya") not in current_pos_options:
        st.session_state["eshik_pozitsiya"] = "O'rta"

    eshik_pozitsiya = st.radio(
        "Eshik pozitsiyasi",
        current_pos_options,
        index=current_pos_options.index(st.session_state["eshik_pozitsiya"]),
        horizontal=True,
        key="eshik_pozitsiya",
        on_change=save_form_data
    )

    eshik_ochilish = st.radio(
        "Eshik ochilishi",
        eshik_ochilish_options,
        index=eshik_ochilish_options.index(st.session_state["eshik_ochilish"]),
        horizontal=True,
        key="eshik_ochilish",
        on_change=save_form_data
    )

    agregat = st.selectbox(
        "Agregat (Sovutish tizimi)",
        agregat_options,
        index=agregat_options.index(st.session_state["agregat"]),
        key="agregat",
        on_change=save_form_data
    )

    agregat_joyi = st.radio(
        "Agregat joylashuvi",
        agregat_joyi_options,
        index=agregat_joyi_options.index(st.session_state["agregat_joyi"]),
        horizontal=True,
        key="agregat_joyi",
        on_change=save_form_data
    )

st.divider()

st.subheader("3. Loyiha sozlamalari")
g1, g2 = st.columns(2)
project_name = g1.text_input("Loyiha nomi", key="project_name", on_change=save_form_data)
room_code = g2.text_input("Loyiha kodi", key="room_code", on_change=save_form_data)

st.divider()

# =========================================================
# AI ASSIST
# =========================================================
st.subheader("4. AI Texnik Tavsiya (Groq)")
ai1, ai2, ai3 = st.columns(3)

mahsulot_turi = ai1.selectbox(
    "Mahsulot turi",
    mahsulot_options,
    index=mahsulot_options.index(st.session_state["mahsulot_turi"]),
    key="mahsulot_turi",
    on_change=save_form_data
)

saqlash_temp = ai2.text_input(
    "Talab qilinadigan harorat",
    key="saqlash_temp",
    on_change=save_form_data
)

ochilish_soni = ai3.selectbox(
    "Kunlik eshik ochilish soni",
    ochilish_options,
    index=ochilish_options.index(st.session_state["ochilish_soni"]),
    key="ochilish_soni",
    on_change=save_form_data
)

ai4, ai5 = st.columns(2)

hudud = ai4.selectbox(
    "Hudud / iqlim",
    hudud_options,
    index=hudud_options.index(st.session_state["hudud"]),
    key="hudud",
    on_change=save_form_data
)

namlik_talabi = ai5.selectbox(
    "Namlik talabi",
    namlik_options,
    index=namlik_options.index(st.session_state["namlik_talabi"]),
    key="namlik_talabi",
    on_change=save_form_data
)

if "ai_result" not in st.session_state:
    st.session_state.ai_result = None

if st.button("🤖 AI TAVSIYA OLISH"):
    with st.spinner("Groq AI texnik tavsiya tayyorlamoqda..."):
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

st.divider()

# =========================================================
# CALCULATIONS
# =========================================================
wall_mm = mm_val(d_qalin)
ceil_mm = mm_val(p_qalin)
floor_mm = mm_val(pol_qalin) if pol_bor else 0
door_w_mm, door_h_mm = door_dimensions(eshik)

hajm = round(L * W * H, 2)
s_devor = round(2 * (L + W) * H, 2)
s_patalok = round(L * W, 2)
s_pol = round(L * W, 2) if pol_bor else 0

inner_L_mm = max(0, m_to_mm(L) - (2 * wall_mm))
inner_W_mm = max(0, m_to_mm(W) - (2 * wall_mm))
inner_H_mm = max(0, m_to_mm(H) - ceil_mm - (floor_mm if pol_bor else 0))

wall_layout_L = panel_count_linear(L, panel_width_m)
wall_layout_W = panel_count_linear(W, panel_width_m)

devor_panels_total = (wall_layout_L["total_panels"] * 2) + (wall_layout_W["total_panels"] * 2)
patalok_panels_total = math.ceil(W / panel_width_m)
pol_panels_total = math.ceil(W / panel_width_m) if pol_bor else 0

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
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Hajm</div><div class="metric-value">{hajm} m³</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Devor maydoni</div><div class="metric-value">{s_devor} m²</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Patalok maydoni</div><div class="metric-value">{s_patalok} m²</div></div>', unsafe_allow_html=True)
with m4:
    st.markdown(f'<div class="metric-box"><div class="metric-title">Pol maydoni</div><div class="metric-value">{s_pol} m²</div></div>', unsafe_allow_html=True)

st.divider()

# =========================================================
# TECHNICAL DRAWING
# =========================================================
st.subheader("5. Texnik Chizma Listi")

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
st.caption("Texnik listda har bir tomonda burchak 480 mm qilib olindi, markaziy qism 960 modul bilan bo‘lindi. Eshik faqat reja chizmasida ko‘rsatildi.")

st.divider()

# =========================================================
# SPEC
# =========================================================
st.subheader("6. Panel раскладка va spetsifikatsiya")

t1, t2 = st.columns(2)

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
        st.write(f"**Eshik moduli:** {door_w_mm} mm ({eshik_joyi} tomonda, {eshik_pozitsiya}, {eshik_ochilish})")
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    st.markdown("<div class='tech-table'>", unsafe_allow_html=True)
    st.markdown("### Panel раскладka")
    st.write(f"**Uzun devor (2 ta):** {L:.2f} m")
    st.write(f"- To‘liq panel: {wall_layout_L['full_panels']} ta")
    st.write(f"- Qoldiq panel: {wall_layout_L['remainder_m']:.3f} m")

    st.write(f"**Qisqa devor (2 ta):** {W:.2f} m")
    st.write(f"- To‘liq panel: {wall_layout_W['full_panels']} ta")
    st.write(f"- Qoldiq panel: {wall_layout_W['remainder_m']:.3f} m")

    st.write(f"**Umumiy devor panel soni:** {devor_panels_total} ta")
    st.write(f"**Taxminiy patalok panel soni:** {patalok_panels_total} ta")
    st.write(f"**Taxminiy pol panel soni:** {pol_panels_total if pol_bor else 0} ta")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# =========================================================
# SAVE / RESET
# =========================================================
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

st.divider()

# =========================================================
# FINAL REPORT + TELEGRAM
# =========================================================
if st.button("HISOBLASH VA ADMINGA YUBORISH"):
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

        <p><b>Tashqi o‘lcham:</b> {fmt_m(L)} × {fmt_m(W)} × {fmt_m(H)}</p>
        <p><b>Ichki foydali o‘lcham:</b> {inner_L_mm} × {inner_W_mm} × {inner_H_mm} mm</p>
        <p><b>Kamera hajmi:</b> {hajm} m³</p>

        <hr>

        <p><b>Devor:</b> {d_turi} / {wall_mm} mm — {s_devor} m²</p>
        <p><b>Patalok:</b> {p_turi} / {ceil_mm} mm — {s_patalok} m²</p>
        <p><b>Pol:</b> {pol_turi if pol_bor else "Mavjud emas"} {" / " + str(floor_mm) + " mm" if pol_bor else ""} — {s_pol} m²</p>

        <hr>

        <p><b>Eshik:</b> {eshik} {f"({door_w_mm}x{door_h_mm} mm)" if eshik != "Yo'q" else ""}</p>
        <p><b>Eshik joylashuvi:</b> {eshik_joyi}</p>
        <p><b>Eshik pozitsiyasi:</b> {eshik_pozitsiya if eshik != "Yo'q" else "Mavjud emas"}</p>
        <p><b>Eshik ochilishi:</b> {eshik_ochilish}</p>

        <p><b>Agregat:</b> {agregat}</p>
        <p><b>Agregat joylashuvi:</b> {agregat_joyi if agregat != "Yo'q" else "Mavjud emas"}</p>

        <hr>

        <p><b>Uzunlik tomoni segmentlari:</b> {top_report}</p>
        <p><b>En tomoni segmentlari:</b> {right_report}</p>

        <p><b>Panel ishchi eni:</b> {panel_width_m:.2f} m</p>
        <p><b>Umumiy devor panel soni:</b> {devor_panels_total} ta</p>
        <p><b>Taxminiy patalok panel soni:</b> {patalok_panels_total} ta</p>
        <p><b>Taxminiy pol panel soni:</b> {pol_panels_total if pol_bor else 0} ta</p>

        {ai_summary}

        <hr>

        <p><b>Montaj:</b> {"Ha" if eshik != "Yo'q" or agregat != "Yo'q" else "So'ralmagan"}</p>
        <p><b>Texnik izoh:</b> Har bir tomonda burchak 480 mm, markaziy qism 960 modul bo‘yicha ajratildi. Eshik moduli aniq ko‘rsatildi. Eshik ochilish yo‘nalishi reja chizmasida ko‘rsatildi. Ichki foydali o‘lchamlar chizmada berildi.</p>
    </div>
    """, unsafe_allow_html=True)

    if tg_ok:
        st.success("Ma'lumot Telegram kanalga yuborildi.")
    else:
        st.error(f"Telegramga yuborilmadi: {tg_msg}")

    save_form_data()
    st.toast("Ma'lumotlar tayyor. Saqlandi va yuborildi.")