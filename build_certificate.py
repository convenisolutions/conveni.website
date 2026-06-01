"""Build zertifikat-stefanou.docx with a recreated SU logo."""
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Pt, Mm, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io, os

# ── 1. Build the SU logo as a PNG in memory ─────────────────────────────────
W, H = 300, 300
bg = (26, 42, 74)        # dark navy, matches the letter logo
white = (255, 255, 255)

img = Image.new("RGB", (W, H), bg)
draw = ImageDraw.Draw(img)

# Try to load a bold font; fall back to default
def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

# "SU" large
font_su = load_font(130)
bbox = draw.textbbox((0, 0), "SU", font=font_su)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((W - tw) // 2, 30), "SU", fill=white, font=font_su)

# German flag strip
flag_y = 175
strip_h = 12
draw.rectangle([60, flag_y, 240, flag_y + strip_h], fill=(0, 0, 0))
draw.rectangle([60, flag_y + strip_h, 240, flag_y + 2 * strip_h], fill=(221, 0, 0))
draw.rectangle([60, flag_y + 2 * strip_h, 240, flag_y + 3 * strip_h], fill=(255, 206, 0))

# "NÖRDLICHE WEINSTRASSE" small
font_sub = load_font(22)
for i, line in enumerate(["NÖRDLICHE", "WEINSTRASSE"]):
    bbox2 = draw.textbbox((0, 0), line, font=font_sub)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((W - tw2) // 2, 222 + i * 28), line, fill=white, font=font_sub)

buf = io.BytesIO()
img.save(buf, format="PNG")
buf.seek(0)

# ── 2. Build the Word document ──────────────────────────────────────────────
doc = Document()

# Page margins: 2.5 cm all around
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.0)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

def set_font(run, name="Times New Roman", size=12, bold=False, italic=False, color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

# ── Header table: address left | logo right ──────────────────────────────
tbl = doc.add_table(rows=1, cols=2)
tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
tbl.style = "Table Grid"

# Remove table borders
for row in tbl.rows:
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            border_el = OxmlElement(f"w:{side}")
            border_el.set(qn("w:val"), "none")
            tcBorders.append(border_el)
        tcPr.append(tcBorders)

left_cell  = tbl.cell(0, 0)
right_cell = tbl.cell(0, 1)

# Left: address (italic)
addr_lines = [
    "An David Stefanou",
    "Geschäftsführer",
    "Schüler Union Nördliche Weinstraße",
]
left_cell.paragraphs[0].clear()
for i, line in enumerate(addr_lines):
    p = left_cell.paragraphs[0] if i == 0 else left_cell.add_paragraph()
    run = p.add_run(line)
    set_font(run, size=11, italic=True)

# Right: logo image, right-aligned
right_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
right_cell.paragraphs[0].clear()
run_img = right_cell.paragraphs[0].add_run()
run_img.add_picture(buf, width=Cm(4.0))

doc.add_paragraph()   # spacer

# ── Date ─────────────────────────────────────────────────────────────────────
p_date = doc.add_paragraph()
p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p_date.add_run("Bad Dürkheim, 1. Juni 2026")
set_font(r, size=12)

doc.add_paragraph()

# ── Subject ───────────────────────────────────────────────────────────────────
p_subj = doc.add_paragraph()
r = p_subj.add_run("Bescheinigung über die Funktion als Geschäftsführer")
set_font(r, size=12, bold=True)
r.font.underline = True

doc.add_paragraph()

# ── Body ──────────────────────────────────────────────────────────────────────
def body_para(text, bold=False, center=False):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_font(r, size=12, bold=bold)
    return p

body_para("Hiermit wird bestätigt, dass")
body_para("David Stefanou", bold=True, center=True)

p = doc.add_paragraph()
r1 = p.add_run("seit ")
set_font(r1, size=12)
r2 = p.add_run("November 2025")
set_font(r2, size=12, bold=True)
r3 = p.add_run(" das Amt des ")
set_font(r3, size=12)
r4 = p.add_run("Geschäftsführers")
set_font(r4, size=12, bold=True)
r5 = p.add_run(" des Kreisverbandes ")
set_font(r5, size=12)
r6 = p.add_run("Schüler Union Nördliche Weinstraße")
set_font(r6, size=12, bold=True)
r7 = p.add_run(" innehat.")
set_font(r7, size=12)

body_para(
    "David Stefanou nimmt diese Funktion mit Verantwortung und Engagement wahr und "
    "ist offiziell als Mitglied des Kreisvorstands der Schüler Union Nördliche "
    "Weinstraße eingetragen."
)
body_para(
    "Diese Bescheinigung wird auf Wunsch ausgestellt und dient als Nachweis über die "
    "genannte Funktion innerhalb der Organisation."
)

doc.add_paragraph()

# ── Closing ───────────────────────────────────────────────────────────────────
p = doc.add_paragraph()
r = p.add_run("Mit freundlichen Grüßen,")
set_font(r, size=12)

# Signature space
for _ in range(4):
    doc.add_paragraph()

# Signature line (using underscores as a line)
p_sig = doc.add_paragraph()
r = p_sig.add_run("_" * 35)
set_font(r, size=12)

p_name = doc.add_paragraph()
r = p_name.add_run("Darian Friedrich")
set_font(r, size=12)

p_title = doc.add_paragraph()
r = p_title.add_run("Kreisvorsitzender")
set_font(r, size=12, italic=True)

p_org = doc.add_paragraph()
r = p_org.add_run("Schüler Union Nördliche Weinstraße")
set_font(r, size=12, italic=True)

# ── Save ──────────────────────────────────────────────────────────────────────
out_path = "/home/user/conveni.website/zertifikat-stefanou.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
