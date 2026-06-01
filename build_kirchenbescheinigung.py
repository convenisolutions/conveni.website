"""Build kirchenbescheinigung-stefanou.docx – Protestant church style."""
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Pt, Mm, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io, os

# ── 1. Church logo: cross + church name ─────────────────────────────────────
W, H = 500, 200
bg      = (255, 255, 255)
red     = (140, 20, 20)      # Burgundy – Evangelische Kirche der Pfalz style
dark    = (60, 60, 60)

img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

# Draw cross (left side of logo)
cx, cy = 60, 100
arm = 42
thick = 14
# vertical
draw.rectangle([cx - thick//2, cy - arm, cx + thick//2, cy + arm], fill=red)
# horizontal
draw.rectangle([cx - arm, cy - thick//2, cx + arm, cy + thick//2], fill=red)

# Church name text (right of cross)
font_main = load_font(22, bold=True)
font_sub  = load_font(16, bold=False)
font_tiny = load_font(13, bold=False)

draw.text((120, 28),  "Protestantische Kirchengemeinde", fill=red,  font=font_main)
draw.text((120, 58),  "Gimmeldingen-Königsbach",         fill=red,  font=font_main)

# Thin separator line
draw.rectangle([120, 92, 480, 94], fill=red)

draw.text((120, 100), "Kirchplatz 2 · 67435 Neustadt a.d. Weinstraße",
          fill=dark, font=font_tiny)
draw.text((120, 118), "Tel. 06321/68655 · pfarramt.gimmeldingen@evkirchepfalz.de",
          fill=dark, font=font_tiny)

buf = io.BytesIO()
img.save(buf, format="PNG")
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
    r.font.name    = "Times New Roman"
    r.font.size    = Pt(size)
    r.font.bold    = bold
    r.font.italic  = italic
    if color:
        r.font.color.rgb = RGBColor(*color)
    return r

BURGUNDY = (140, 20, 20)

# ── Logo ──────────────────────────────────────────────────────────────────────
p_logo = doc.add_paragraph()
p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
p_logo.paragraph_format.space_after = Pt(2)
p_logo.add_run().add_picture(buf, width=Cm(13.0))

# Thick red top border line (via paragraph bottom border on logo para)
# We'll add a horizontal rule paragraph instead
p_rule = doc.add_paragraph()
p_rule.paragraph_format.space_before = Pt(0)
p_rule.paragraph_format.space_after  = Pt(10)
pPr = p_rule._p.get_or_add_pPr()
pBdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"),   "single")
bottom.set(qn("w:sz"),    "12")
bottom.set(qn("w:space"), "1")
bottom.set(qn("w:color"), "8C1414")
pBdr.append(bottom)
pPr.append(pBdr)

# ── Date ──────────────────────────────────────────────────────────────────────
para("Gimmeldingen, 1. Juni 2026",
     align=WD_ALIGN_PARAGRAPH.RIGHT, size=12, space_after=8)

# ── Subject ───────────────────────────────────────────────────────────────────
para("Ehrenamtliche Tätigkeitsbescheinigung",
     bold=True, underline=True, size=13,
     color=BURGUNDY, space_before=4, space_after=10)

# ── Body ──────────────────────────────────────────────────────────────────────
para("Hiermit wird bestätigt, dass", size=12, space_after=4)

p_name = para(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=4)
add_run(p_name, "David Stefanou", bold=True, size=14, color=BURGUNDY)

p_body1 = doc.add_paragraph()
p_body1.paragraph_format.space_after = Pt(6)
add_run(p_body1, "seit dem ")
add_run(p_body1, "15. März 2024", bold=True)
add_run(p_body1, " ehrenamtlich und engagiert in unserer Kirchengemeinde ")
add_run(p_body1, "Protestantische Kirchengemeinde Gimmeldingen-Königsbach", bold=True)
add_run(p_body1, " aktiv ist.")

para(
    "Sein Engagement ist ein wertvoller Beitrag zum Leben unserer Gemeinde. "
    "Wir sind dankbar für seine verlässliche Mitarbeit und sein Engagement.",
    size=12, space_after=6
)

para(
    "Diese Bescheinigung wird auf Wunsch ausgestellt und dient als offizieller "
    "Nachweis über die ehrenamtliche Tätigkeit innerhalb unserer Kirchengemeinde.",
    size=12, space_after=14
)

# ── Closing ───────────────────────────────────────────────────────────────────
para("Mit freundlichen Grüßen und Gottes Segen,", size=12, space_after=2)

# Signature space
for _ in range(4):
    doc.add_paragraph()

p_sig = doc.add_paragraph()
p_sig.paragraph_format.space_after = Pt(1)
add_run(p_sig, "_" * 35)

para("Thomas Klein", bold=True, size=12, space_after=1)
para("Pfarrer", italic=True, size=12, space_after=1)
para("Protestantische Kirchengemeinde Gimmeldingen-Königsbach",
     italic=True, size=11, color=(80, 80, 80))

# ── Footer line ───────────────────────────────────────────────────────────────
p_foot = doc.add_paragraph()
pPr2 = p_foot._p.get_or_add_pPr()
pBdr2 = OxmlElement("w:pBdr")
top = OxmlElement("w:top")
top.set(qn("w:val"),   "single")
top.set(qn("w:sz"),    "6")
top.set(qn("w:space"), "1")
top.set(qn("w:color"), "8C1414")
pBdr2.append(top)
pPr2.append(pBdr2)
p_foot.paragraph_format.space_before = Pt(20)

r_foot = p_foot.add_run(
    "Protestantische Kirchengemeinde Gimmeldingen-Königsbach  ·  "
    "Kirchplatz 2, 67435 Neustadt a.d. Weinstraße  ·  Tel. 06321/68655  ·  "
    "pfarramt.gimmeldingen@evkirchepfalz.de"
)
r_foot.font.name  = "Times New Roman"
r_foot.font.size  = Pt(8)
r_foot.font.color.rgb = RGBColor(100, 100, 100)
p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/home/user/conveni.website/kirchenbescheinigung-stefanou.docx"
doc.save(out)
print(f"Saved: {out}")
