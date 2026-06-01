"""Build kirchenbescheinigung-stefanou.docx with the exact church logo."""
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io, os

DARK_BLUE  = (26,  55, 109)   # dark navy
LIGHT_BLUE = (41, 128, 185)   # medium blue
WHITE      = (255, 255, 255)
BLACK      = (20,  20,  20)
NAVY       = (26,  55, 109)

# ── Load font helper ─────────────────────────────────────────────────────────
def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"    if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"            if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

# ── 1. Recreate the logo ─────────────────────────────────────────────────────
# Canvas: 580 x 120  (symbol ~100px wide | text right side)
W, H = 580, 120
logo = Image.new("RGBA", (W, H), (255, 255, 255, 0))
d    = ImageDraw.Draw(logo)

# Two overlapping book/bible page shapes
# Dark navy page (back, left)
dark_pts  = [(4, 4), (74, 4), (68, 112), (4, 112)]
# Light blue page (front, right), overlapping
light_pts = [(38, 8), (108, 4), (108, 108), (42, 112)]

d.polygon(dark_pts,  fill=DARK_BLUE)
d.polygon(light_pts, fill=LIGHT_BLUE)

# White cross on the dark blue page
cx, cy   = 36, 58
v_arm, h_arm = 32, 24
thick    = 8
d.rectangle([cx - thick//2, cy - v_arm, cx + thick//2, cy + v_arm], fill=WHITE)
d.rectangle([cx - h_arm,   cy - thick//2, cx + h_arm, cy + thick//2], fill=WHITE)

# Text: "Prot. Pfarramt  Gimmeldingen-" / "Königsbach-Mußbach"
f_name = load_font(26, bold=True)
f_sub  = load_font(26, bold=True)
d.text((124, 18), "Prot. Pfarramt  Gimmeldingen-", fill=BLACK, font=f_name)
d.text((124, 52), "Königsbach-Mußbach",            fill=BLACK, font=f_sub)

buf = io.BytesIO()
logo.save(buf, format="PNG")
buf.seek(0)

# ── 2. Build Word document ───────────────────────────────────────────────────
doc = Document()

for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

def para(text="", bold=False, italic=False, size=12, align=WD_ALIGN_PARAGRAPH.LEFT,
         color=None, underline=False, space_before=0, space_after=4):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    if text:
        r = p.add_run(text)
        r.font.name      = "Times New Roman"
        r.font.size      = Pt(size)
        r.font.bold      = bold
        r.font.italic    = italic
        r.font.underline = underline
        if color:
            r.font.color.rgb = RGBColor(*color)
    return p

def add_run(p, text, bold=False, italic=False, size=12, color=None):
    r = p.add_run(text)
    r.font.name   = "Times New Roman"
    r.font.size   = Pt(size)
    r.font.bold   = bold
    r.font.italic = italic
    if color:
        r.font.color.rgb = RGBColor(*color)
    return r

def hr(color_hex, sz="8", space_before=0, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    sz)
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), color_hex)
    pBdr.append(bot)
    pPr.append(pBdr)
    return p

def hr_top(color_hex, sz="6", space_before=16, space_after=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(2)
    pPr  = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top  = OxmlElement("w:top")
    top.set(qn("w:val"),   "single")
    top.set(qn("w:sz"),    sz)
    top.set(qn("w:space"), "1")
    top.set(qn("w:color"), color_hex)
    pBdr.append(top)
    pPr.append(pBdr)
    return p

# ── Logo ──────────────────────────────────────────────────────────────────────
p_logo = doc.add_paragraph()
p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
p_logo.paragraph_format.space_after = Pt(2)
p_logo.add_run().add_picture(buf, width=Cm(13.5))

# Navy separator line below logo
hr("1A376D", sz="12", space_before=0, space_after=10)

# ── Date ──────────────────────────────────────────────────────────────────────
para("Gimmeldingen, 1. Juni 2026",
     align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, space_after=8)

# ── Subject ───────────────────────────────────────────────────────────────────
para("Ehrenamtliche Tätigkeitsbescheinigung",
     bold=True, underline=True, size=13,
     color=NAVY, space_before=4, space_after=10)

# ── Body ──────────────────────────────────────────────────────────────────────
para("Hiermit wird bestätigt, dass", size=12, space_after=4)

p_name = para(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=4)
add_run(p_name, "David Stefanou", bold=True, size=14, color=NAVY)

p_b = doc.add_paragraph()
p_b.paragraph_format.space_after = Pt(6)
add_run(p_b, "seit dem ")
add_run(p_b, "15. März 2024", bold=True)
add_run(p_b, " ehrenamtlich und engagiert in unserer Kirchengemeinde ")
add_run(p_b, "Prot. Pfarramt Gimmeldingen-Königsbach-Mußbach", bold=True)
add_run(p_b, " aktiv ist.")

para(
    "Sein Engagement ist ein wertvoller Beitrag zum Leben unserer Gemeinde. "
    "Wir sind dankbar für seine verlässliche Mitarbeit und sein Einsatz.",
    size=12, space_after=6
)
para(
    "Diese Bescheinigung wird auf Wunsch ausgestellt und dient als offizieller "
    "Nachweis über die ehrenamtliche Tätigkeit innerhalb unserer Kirchengemeinde.",
    size=12, space_after=14
)

# ── Closing ───────────────────────────────────────────────────────────────────
para("Mit freundlichen Grüßen und Gottes Segen,", size=12, space_after=2)

# Signature gap
for _ in range(4):
    doc.add_paragraph()

p_sig = doc.add_paragraph()
p_sig.paragraph_format.space_after = Pt(1)
add_run(p_sig, "_" * 35)

para("Thomas Klein",                                bold=True,  size=12, space_after=1)
para("Pfarrer",                                     italic=True, size=12, space_after=1)
para("Prot. Pfarramt Gimmeldingen-Königsbach-Mußbach",
     italic=True, size=11, color=(80, 80, 80))

# ── Footer ────────────────────────────────────────────────────────────────────
p_foot = hr_top("1A376D", sz="6", space_before=20, space_after=0)
r_f = p_foot.add_run(
    "Prot. Pfarramt Gimmeldingen-Königsbach-Mußbach  ·  "
    "Kirchplatz 2, 67435 Neustadt a.d. Weinstraße  ·  "
    "Tel. 06321/68655  ·  pfarramt.gimmeldingen@evkirchepfalz.de"
)
r_f.font.name      = "Times New Roman"
r_f.font.size      = Pt(8)
r_f.font.color.rgb = RGBColor(100, 100, 100)
p_foot.alignment   = WD_ALIGN_PARAGRAPH.CENTER

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/home/user/conveni.website/kirchenbescheinigung-stefanou.docx"
doc.save(out)
print(f"Saved: {out}")
