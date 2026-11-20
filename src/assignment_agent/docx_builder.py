"""
VoiceMate Assignment Agent - Pure Python DOCX Document Builder.
Creates genuine, standardized Microsoft Word (.docx) files using Python's standard library
zipfile and OpenXML format without requiring any external third-party dependencies.
"""
import io
import os
import zipfile
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


class PureDocxBuilder:
    """
    Lightweight, dependency-free Microsoft Word (.docx) file generator.
    Produces 100% compliant OpenXML packages that open reliably in MS Word.
    """

    CONTENT_TYPES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    DOCUMENT_RELS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    STYLES_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
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
</w:styles>"""

    @classmethod
    def create_document(
        cls,
        output_path: str,
        title: str,
        sections: List[Dict[str, Any]]
    ) -> str:
        """
        Creates a formatted .docx document and saves it to output_path.
        Each section is a dict with:
          - 'heading': str (optional)
          - 'paragraphs': List[str]
          - 'bullets': List[str] (optional)
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        body_elements: List[str] = []

        # 1. Document Title
        body_elements.append(
            f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="240"/></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="1F3864"/></w:rPr>'
            f'<w:t>{cls._escape(title)}</w:t></w:r></w:p>'
        )
        body_elements.append(
            '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="AAAAAA"/></w:pBdr></w:pPr></w:p>'
        )

        # 2. Sections
        for sec in sections:
            heading = sec.get("heading")
            if heading:
                body_elements.append(
                    f'<w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>'
                    f'<w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1F4E79"/></w:rPr>'
                    f'<w:t>{cls._escape(heading)}</w:t></w:r></w:p>'
                )

            for p_text in sec.get("paragraphs", []):
                for p_sub in str(p_text).split("\n\n"):
                    p_sub_strip = p_sub.strip()
                    if not p_sub_strip:
                        continue
                    body_elements.append(
                        f'<w:p><w:pPr><w:spacing w:after="120"/></w:pPr>'
                        f'<w:r><w:t xml:space="preserve">{cls._escape(p_sub_strip)}</w:t></w:r></w:p>'
                    )

            for bullet in sec.get("bullets", []):
                body_elements.append(
                    f'<w:p><w:pPr><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="60"/></w:pPr>'
                    f'<w:r><w:t>• </w:t></w:r>'
                    f'<w:r><w:t xml:space="preserve">{cls._escape(bullet)}</w:t></w:r></w:p>'
                )

        body_xml = "\n".join(body_elements)
        document_xml = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            f'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">\n'
            f'  <w:body>\n'
            f'{body_xml}\n'
            f'    <w:sectPr>\n'
            f'      <w:pgSz w:w="12240" w:h="15840"/>\n'
            f'      <w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" '
            f'w:header="720" w:footer="720" w:gutter="0"/>\n'
            f'    </w:sectPr>\n'
            f'  </w:body>\n'
            f'</w:document>'
        )

        # Build ZIP (.docx) package
        with zipfile.ZipFile(str(out), "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", cls.CONTENT_TYPES_XML)
            z.writestr("_rels/.rels", cls.RELS_XML)
            z.writestr("word/_rels/document.xml.rels", cls.DOCUMENT_RELS_XML)
            z.writestr("word/styles.xml", cls.STYLES_XML)
            z.writestr("word/document.xml", document_xml.encode("utf-8"))

        return str(out.resolve())

    @staticmethod
    def _escape(text: str) -> str:
        """Escapes XML special characters."""
        if not text:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
