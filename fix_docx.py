"""
Fix: Regenerate Assignment_01_Solution.docx with correct XML structure.
Problem: table rows were not wrapped inside <w:tbl> tags.
"""

import sys, os, zipfile, io, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from datetime import datetime

def xml_escape(text):
    return (str(text)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

def make_run(text, bold=False, color=None, size=None):
    rpr = '<w:rPr>'
    if bold:
        rpr += '<w:b/>'
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if size:
        rpr += f'<w:sz w:val="{size}"/>'
    rpr += '</w:rPr>'
    return f'<w:r>{rpr}<w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r>'

def make_para(runs_xml, style=None, indent=None, shade=None, border_bottom=False, spacing_before=None, spacing_after=None):
    ppr = '<w:pPr>'
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if indent:
        ppr += f'<w:ind w:left="{indent}"/>'
    if shade:
        ppr += f'<w:shd w:val="clear" w:fill="{shade}"/>'
    if border_bottom:
        ppr += '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="AAAAAA"/></w:pBdr>'
    if spacing_before or spacing_after:
        sb = spacing_before or '0'
        sa = spacing_after or '0'
        ppr += f'<w:spacing w:before="{sb}" w:after="{sa}"/>'
    ppr += '</w:pPr>'
    return f'<w:p>{ppr}{runs_xml}</w:p>'

def make_heading(text, level=1):
    colors = {1: '1F3864', 2: '1F4E79', 3: '2E75B6'}
    sizes  = {1: 36, 2: 28, 3: 24}
    runs = make_run(text, bold=True, color=colors.get(level,'000000'), size=sizes.get(level))
    return make_para(runs, style=f'Heading{level}')

def make_table(rows):
    """rows = list of list of cell strings. First row = header."""
    tbl_xml = '<w:tbl>'
    tbl_xml += '''<w:tblPr>
      <w:tblStyle w:val="TableGrid"/>
      <w:tblW w:w="9360" w:type="dxa"/>
      <w:tblBorders>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="AAAAAA"/>
      </w:tblBorders>
    </w:tblPr>'''
    
    for r_idx, row in enumerate(rows):
        is_header = (r_idx == 0)
        tbl_xml += '<w:tr>'
        if is_header:
            tbl_xml += '<w:trPr><w:tblHeader/></w:trPr>'
        col_w = 9360 // max(len(row), 1)
        for cell in row:
            fill = 'D6E4F0' if is_header else 'FFFFFF'
            cell_text = xml_escape(str(cell).replace('**','').replace('*',''))
            tbl_xml += f'''<w:tc>
              <w:tcPr>
                <w:tcW w:w="{col_w}" w:type="dxa"/>
                <w:shd w:val="clear" w:fill="{fill}"/>
              </w:tcPr>
              <w:p><w:r><w:rPr>{'<w:b/>' if is_header else ''}</w:rPr>
              <w:t xml:space="preserve">{cell_text}</w:t></w:r></w:p>
            </w:tc>'''
        tbl_xml += '</w:tr>'
    
    tbl_xml += '</w:tbl>'
    return tbl_xml

def parse_inline_bold(text):
    """Convert **bold** to proper run XML."""
    parts = re.split(r'\*\*(.+?)\*\*', text)
    runs = ''
    for idx, part in enumerate(parts):
        if not part:
            continue
        runs += make_run(part, bold=(idx % 2 == 1))
    return runs if runs else make_run(text)

def md_to_body_elements(md_text):
    """Convert markdown to list of OOXML body elements (paragraphs + tables)."""
    elements = []
    lines = md_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Headings
        if stripped.startswith('#### '):
            elements.append(make_heading(stripped[5:], 3))
            i += 1
        elif stripped.startswith('### '):
            elements.append(make_heading(stripped[4:], 3))
            i += 1
        elif stripped.startswith('## '):
            elements.append(make_heading(stripped[3:], 2))
            i += 1
        elif stripped.startswith('# ') and not stripped.startswith('##'):
            elements.append(make_heading(stripped[2:], 1))
            i += 1
        
        # Horizontal rule
        elif stripped == '---':
            elements.append(make_para('', border_bottom=True))
            i += 1
        
        # Blockquote
        elif stripped.startswith('> '):
            text = stripped[2:].replace('**','')
            runs = make_run(text, bold=True, color='1F4E79')
            elements.append(make_para(runs, indent='720', shade='EBF3FB'))
            i += 1
        
        # Bullet list
        elif stripped.startswith('- ') or stripped.startswith('* '):
            text = stripped[2:]
            runs = parse_inline_bold(text)
            # Simple bullet with indent
            ppr = '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
            bullet_run = make_run('• ', bold=False)
            elements.append(f'<w:p>{ppr}{bullet_run}{runs}</w:p>')
            i += 1
        
        # Numbered list
        elif re.match(r'^\d+\.\s', stripped):
            text = re.sub(r'^\d+\.\s', '', stripped)
            runs = parse_inline_bold(text)
            ppr = '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
            elements.append(f'<w:p>{ppr}{runs}</w:p>')
            i += 1
        
        # Code block
        elif stripped.startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            for cl in code_lines:
                runs = make_run(cl if cl else ' ', color='1F3864')
                ppr = '<w:pPr><w:ind w:left="720"/><w:shd w:val="clear" w:fill="F5F5F5"/></w:pPr>'
                elements.append(f'<w:p>{ppr}{runs}</w:p>')
        
        # Table
        elif stripped.startswith('|') and '|' in stripped:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            # Parse table rows, skip separator rows (---|---|---)
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.split('|') if c.strip()]
                if cells and not all(set(c) <= set('-: ') for c in cells):
                    rows.append(cells)
            if rows:
                elements.append(make_table(rows))
                elements.append(make_para(''))  # spacing after table
        
        # Empty line
        elif stripped == '':
            elements.append('<w:p/>')
            i += 1
        
        # Regular paragraph
        else:
            runs = parse_inline_bold(stripped)
            elements.append(f'<w:p>{runs}</w:p>')
            i += 1
    
    return elements

def build_docx(md_content, output_path):
    body_elements = md_to_body_elements(md_content)
    body_xml = '\n'.join(body_elements)
    
    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document
  xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
  mc:Ignorable="w14 wpc">
  <w:body>
{body_xml}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080"
               w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>'''

    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
          xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        <w:sz w:val="22"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="300" w:after="150"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/><w:sz w:val="36"/><w:color w:val="1F3864"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/><w:sz w:val="28"/><w:color w:val="1F4E79"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="200" w:after="100"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/><w:sz w:val="24"/><w:color w:val="2E75B6"/>
    </w:rPr>
  </w:style>
  <w:style w:type="table" w:styleId="TableGrid">
    <w:name w:val="Table Grid"/>
    <w:tblPr>
      <w:tblBorders>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>
        <w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>
        <w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>
        <w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>
        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      </w:tblBorders>
    </w:tblPr>
  </w:style>
</w:styles>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>'''

    word_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
</Relationships>'''

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', root_rels)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', styles_xml)
        zf.writestr('word/_rels/document.xml.rels', word_rels)

    Path(output_path).write_bytes(buf.getvalue())
    return Path(output_path).stat().st_size


if __name__ == '__main__':
    md_path  = Path('documents/solutions/Assignment_01_Solution.md')
    out_path = Path('documents/solutions/Assignment_01_Solution.docx')

    print("🔧 Reading solution markdown...")
    md_content = md_path.read_text(encoding='utf-8')

    print("📄 Building valid DOCX (fixed XML structure)...")
    size = build_docx(md_content, str(out_path))

    print(f"✅ DOCX saved: {out_path}  ({size:,} bytes)")
    print("🎉 Microsoft Word এখন ঠিকমতো open করতে পারবে!")
