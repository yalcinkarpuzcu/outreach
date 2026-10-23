"""Build a Workiom-branded .docx from a simple markdown file on top of the Workiom template package."""
import os, re, shutil, sys
from xml.sax.saxutils import escape
from PIL import Image

TPL, MD, IMGDIR, OUT = sys.argv[1:5]
BUILD = OUT + ".build"
NAVY, PURPLE, LINE, BAND = "231F61", "9030E0", "D9D6EE", "F5F4FB"
W_TEXT = 9900          # usable width in twips (template body uses -630 left indent)
IND = -630

shutil.rmtree(BUILD, ignore_errors=True)
shutil.copytree(TPL, BUILD)
WD = os.path.join(BUILD, "word")

# ── styles ────────────────────────────────────────────────────────────────────
def rfont(f): return f'<w:rFonts w:ascii="{f}" w:cs="{f}" w:eastAsia="{f}" w:hAnsi="{f}"/>'
styles = open(os.path.join(WD, "styles.xml"), encoding="utf-8").read()
def set_style(sid, body):
    global styles
    styles, n = re.subn(rf'<w:style [^>]*w:styleId="{sid}".*?</w:style>', body, styles, flags=re.S)
    if not n:
        styles = styles.replace("</w:styles>", body + "</w:styles>")
set_style("Normal", f'<w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="normal"/>'
          f'<w:pPr><w:spacing w:after="120" w:line="288" w:lineRule="auto"/><w:ind w:left="{IND}" w:firstLine="0"/></w:pPr>'
          f'<w:rPr>{rfont("Rubik")}<w:color w:val="{NAVY}"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="tr-TR"/></w:rPr></w:style>')
set_style("Title", f'<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
          f'<w:pPr><w:keepNext/><w:spacing w:before="600" w:after="120" w:line="240" w:lineRule="auto"/></w:pPr>'
          f'<w:rPr>{rfont("Rubik")}<w:color w:val="{NAVY}"/><w:sz w:val="60"/><w:szCs w:val="60"/></w:rPr></w:style>')
set_style("Subtitle", f'<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
          f'<w:pPr><w:keepNext/><w:spacing w:after="360"/></w:pPr>'
          f'<w:rPr>{rfont("Rubik SemiBold")}<w:color w:val="{NAVY}"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>')
set_style("Heading1", f'<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
          f'<w:pPr><w:keepNext/><w:keepLines/><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" w:color="{PURPLE}"/></w:pBdr>'
          f'<w:spacing w:before="560" w:after="240"/><w:outlineLvl w:val="0"/></w:pPr>'
          f'<w:rPr>{rfont("Rubik SemiBold")}<w:color w:val="{NAVY}"/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>')
set_style("Heading2", f'<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/>'
          f'<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>'
          f'<w:rPr>{rfont("Rubik SemiBold")}<w:color w:val="{NAVY}"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>')
set_style("Caption", f'<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/>'
          f'<w:pPr><w:spacing w:before="60" w:after="240"/></w:pPr>'
          f'<w:rPr><w:i/><w:color w:val="6B6893"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr></w:style>')
open(os.path.join(WD, "styles.xml"), "w", encoding="utf-8").write(styles)

# ── numbering ────────────────────────────────────────────────────────────────
num_xml = open(os.path.join(WD, "numbering.xml"), encoding="utf-8").read()
num_head = num_xml.split("/>")[0] if num_xml.rstrip().endswith("/>") else None
abstract = (
    f'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
    f'<w:numFmt w:val="bullet"/><w:lvlText w:val="●"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="-270" w:hanging="300"/></w:pPr>'
    f'<w:rPr>{rfont("Arial")}<w:color w:val="{PURPLE}"/><w:sz w:val="14"/></w:rPr></w:lvl></w:abstractNum>'
    f'<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
    f'<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="-270" w:hanging="360"/></w:pPr>'
    f'<w:rPr>{rfont("Rubik SemiBold")}<w:color w:val="{PURPLE}"/></w:rPr></w:lvl></w:abstractNum>')
nums = []
def new_num(kind):
    nid = len(nums) + 1
    if kind == "ol":
        nums.append(f'<w:num w:numId="{nid}"><w:abstractNumId w:val="2"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
    else:
        nums.append(f'<w:num w:numId="{nid}"><w:abstractNumId w:val="1"/></w:num>')
    return nid

# ── inline markdown → runs ───────────────────────────────────────────────────
def runs(text, size=None, color=None, bold_font="Rubik SemiBold", base_font=None, white=False):
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        rpr = ""
        if i % 2 == 1:
            rpr += rfont(bold_font)
        elif base_font:
            rpr += rfont(base_font)
        if white:
            rpr += '<w:color w:val="FFFFFF"/>'
        elif color:
            rpr += f'<w:color w:val="{color}"/>'
        if size:
            rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(part)}</w:t></w:r>')
    return "".join(out)

def para(text, style=None, extra_ppr="", **kw):
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + extra_ppr
    return f'<w:p><w:pPr>{ppr}</w:pPr>{runs(text, **kw)}</w:p>'

# ── tables ───────────────────────────────────────────────────────────────────
def table(rows):
    header, body = rows[0], rows[1:]
    ncol = len(header)
    weights = []
    for c in range(ncol):
        L = [len(re.sub(r"\*\*", "", r[c])) for r in rows if c < len(r)]
        weights.append(max(13, min(60, (sum(L) / len(L)) ** 0.85 + 4)))
    tot = sum(weights)
    widths = [int(W_TEXT * w / tot) for w in weights]
    widths[-1] = W_TEXT - sum(widths[:-1])
    # never split a word: each column at least as wide as its longest word (bold ≈ 105 twips/char at 8.5pt)
    minw = [max(len(w) for r in rows if c < len(r) for w in (re.sub(r"\*\*", "", r[c]).split() or [""])) * 105 + 260
            for c in range(ncol)]
    for c in range(ncol):
        short = minw[c] - widths[c]
        if short > 0:
            donor = max((d for d in range(ncol) if d != c), key=lambda d: widths[d] - minw[d])
            widths[c] += short; widths[donor] -= short
    b = f'w:val="single" w:sz="4" w:space="0" w:color="{LINE}"'
    x = [f'<w:tbl><w:tblPr><w:tblW w:w="{W_TEXT}" w:type="dxa"/><w:tblInd w:w="{IND}" w:type="dxa"/>'
         f'<w:tblBorders><w:top {b}/><w:left {b}/><w:bottom {b}/><w:right {b}/><w:insideH {b}/><w:insideV {b}/></w:tblBorders>'
         f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="80" w:type="dxa"/><w:left w:w="110" w:type="dxa"/>'
         f'<w:bottom w:w="80" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>']
    x += [f'<w:gridCol w:w="{w}"/>' for w in widths]
    x.append("</w:tblGrid>")
    for ri, r in enumerate(rows):
        hdr = ri == 0
        fill = NAVY if hdr else (BAND if ri % 2 == 0 else "FFFFFF")
        x.append('<w:tr>' + ('<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if hdr else '<w:trPr><w:cantSplit/></w:trPr>'))
        for c in range(ncol):
            cell = r[c] if c < len(r) else ""
            content = runs(f"**{cell}**" if hdr else cell, size=17, white=hdr)
            x.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[c]}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>'
                     f'<w:p><w:pPr><w:spacing w:after="0" w:line="252" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="0"/></w:pPr>{content}</w:p></w:tc>')
        x.append("</w:tr>")
    x.append("</w:tbl>")
    x.append('<w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>')
    return "".join(x)

# ── images ───────────────────────────────────────────────────────────────────
rels = open(os.path.join(WD, "_rels", "document.xml.rels"), encoding="utf-8").read()
img_rels, img_count = [], [0]
def image(fname, caption):
    img_count[0] += 1
    n = img_count[0]
    rid = f"rIdImg{n}"
    shutil.copy(os.path.join(IMGDIR, fname), os.path.join(WD, "media", f"diagram{n}.png"))
    img_rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/diagram{n}.png"/>')
    w, h = Image.open(os.path.join(IMGDIR, fname)).size
    cx = int(W_TEXT / 1440 * 914400)
    cy = int(cx * h / w)
    drawing = (f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
               f'<wp:docPr id="{100+n}" name="Diyagram {n}" descr="{escape(caption)}"/>'
               f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
               f'<pic:nvPicPr><pic:cNvPr id="{100+n}" name="diagram{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
               f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>')
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0"/></w:pPr><w:r>{drawing}</w:r></w:p>'
            + para(caption, "Caption"))

# ── markdown → body ──────────────────────────────────────────────────────────
lines = open(MD, encoding="utf-8").read().split("\n")
body, i = [], 0
sections = [l[3:].strip() for l in lines if l.startswith("## ")]
cover_done = False
while i < len(lines):
    l = lines[i]
    if l.startswith("# "):
        body.append(para(l[2:].strip(), "Title"))
    elif l.startswith("@sub "):
        body.append(para(l[5:].strip(), "Subtitle"))
    elif l.startswith("@meta "):
        body.append(para(l[6:].strip(), size=20, color="6B6893"))
        # table of contents (static) on the cover page
        body.append(para("İçindekiler", "Heading2", extra_ppr='<w:spacing w:before="720" w:after="120"/>'))
        nid = new_num("ol")
        for s in sections:
            body.append(f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{nid}"/></w:numPr><w:spacing w:after="80"/></w:pPr>{runs(s)}</w:p>')
        body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        first_h1 = True
    elif l.startswith("## "):
        if 'first_h1' in dir() and first_h1:
            body.append(para(l[3:].strip(), "Heading1", extra_ppr='<w:spacing w:before="0" w:after="240"/>')); first_h1 = False; i += 1; continue
        body.append(para(l[3:].strip(), "Heading1"))
    elif l.startswith("### "):
        body.append(para(l[4:].strip(), "Heading2"))
    elif l.startswith("@img "):
        f, cap = l[5:].split("|", 1)
        body.append(image(f.strip(), cap.strip()))
    elif l.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"-+", c) for c in cells):
                rows.append(cells)
            i += 1
        body.append(table(rows))
        continue
    elif re.match(r"(\d+\.|-) ", l):
        kind = "ol" if l[0].isdigit() else "ul"
        nid = new_num(kind)
        while i < len(lines) and re.match(r"(\d+\.|-) ", lines[i]):
            t = re.sub(r"^(\d+\.|-) ", "", lines[i])
            body.append(f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{nid}"/></w:numPr><w:spacing w:after="80"/></w:pPr>{runs(t)}</w:p>')
            i += 1
        body.append('<w:p><w:pPr><w:spacing w:after="40"/></w:pPr></w:p>')
        continue
    elif l.strip():
        body.append(para(l.strip()))
    i += 1

# ── assemble ─────────────────────────────────────────────────────────────────
doc = open(os.path.join(WD, "document.xml"), encoding="utf-8").read()
head = doc[: doc.index("<w:body>") + len("<w:body>")]
sect = re.search(r"<w:sectPr.*?</w:sectPr>", doc, re.S).group(0)
sect = re.sub(r'w:bottom="\d+"', 'w:bottom="2300"', sect)
if 'w:gutter' not in sect: sect = sect.replace('<w:pgMar ', '<w:pgMar w:gutter="0" ')   # keep text clear of the footer artwork
open(os.path.join(WD, "document.xml"), "w", encoding="utf-8").write(head + "".join(body) + sect + "</w:body></w:document>")

open(os.path.join(WD, "numbering.xml"), "w", encoding="utf-8").write(
    num_xml.rstrip()[:-2] + ">" + abstract + "".join(nums) + "</w:numbering>")
open(os.path.join(WD, "_rels", "document.xml.rels"), "w", encoding="utf-8").write(
    rels.replace("</Relationships>", "".join(img_rels) + "</Relationships>"))
ct_path = os.path.join(BUILD, "[Content_Types].xml")
ct = open(ct_path, encoding="utf-8").read()
if 'Extension="png"' not in ct:
    ct = ct.replace("<Default ", '<Default ContentType="image/png" Extension="png"/><Default ', 1)
open(ct_path, "w", encoding="utf-8").write(ct)

if os.path.exists(OUT):
    os.remove(OUT)
shutil.make_archive(OUT, "zip", BUILD)
os.rename(OUT + ".zip", OUT)
print("ok", OUT, len(body), "blocks,", len(nums), "lists,", img_count[0], "images")
