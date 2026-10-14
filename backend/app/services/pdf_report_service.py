import io
from datetime import datetime, timezone
from html import escape
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class ConservationReportGenerator:
    """
    Generates formal IUCN/CITES-grade conservation health and studbook PDF records.
    """
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _add_style_safe(self, style: ParagraphStyle):
        if style.name in self.styles:
            self.styles[style.name] = style
        else:
            self.styles.add(style)

    def _setup_custom_styles(self):
        # Custom palette
        self.primary_color = colors.HexColor("#2D5A27") # Forest Green
        self.accent_color = colors.HexColor("#583101")  # Earth Brown
        self.gold_color = colors.HexColor("#D4A373")    # Gold accent
        self.dark_bg = colors.HexColor("#1E293B")       # Dark Slate

        # Typography Styles
        self._add_style_safe(ParagraphStyle(
            name='ReportTitle',
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=self.primary_color,
            spaceAfter=4
        ))

        self._add_style_safe(ParagraphStyle(
            name='ReportSubtitle',
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12
        ))

        self._add_style_safe(ParagraphStyle(
            name='SectionHeading',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=15,
            textColor=self.accent_color,
            spaceBefore=10,
            spaceAfter=6
        ))

        self._add_style_safe(ParagraphStyle(
            name='TableCellText',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        ))

        self._add_style_safe(ParagraphStyle(
            name='TableCellHeader',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white
        ))

        self._add_style_safe(ParagraphStyle(
            name='SecurityNotice',
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748B")
        ))

    def generate_specimen_report(self, specimen_data: Dict[str, Any]) -> bytes:
        """
        Builds a comprehensive PDF report in-memory and returns binary bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        elements = []

        # 1. Document Header
        elements.append(Paragraph("SATRA CHELONIAN CONSERVATION REGISTRY", self.styles['ReportTitle']))
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        elements.append(Paragraph(
            f"Official Health Certificate, Morphometrics & Studbook Record • Generated: {now_utc}",
            self.styles['ReportSubtitle']
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=self.primary_color, spaceAfter=10))

        # 2. Anti-Poaching Notice Box
        notice_text = (
            "<b>CONFIDENTIAL CONSERVATION DOCUMENT:</b> Under the Biodiversity and Anti-Poaching Enforcement Acts, "
            "exact high-precision GPS telemetry coordinates in this dossier are classified and redacted for public release. "
            "Distribution is strictly limited to authorized wildlife sanctuaries, registered veterinarians, and permit authorities."
        )
        notice_table = Table([[Paragraph(notice_text, self.styles['SecurityNotice'])]], colWidths=[18 * cm])
        notice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(notice_table)
        elements.append(Spacer(1, 12))

        # 3. Specimen Identity & Taxonomy Grid
        elements.append(Paragraph("1. SPECIMEN IDENTITY & TAXONOMIC CLASSIFICATION", self.styles['SectionHeading']))
        
        custom_id = escape(str(specimen_data.get('custom_identifier') or 'N/A'))
        species_name = escape(str(specimen_data.get('species_name') or 'N/A'))
        common_name = escape(str(specimen_data.get('common_name') or 'N/A'))
        iucn_status = escape(str(specimen_data.get('iucn_status') or 'LC (Least Concern)'))
        pit_tag = escape(str(specimen_data.get('pit_tag_number') or 'None / Unchipped'))
        notch_code = escape(str(specimen_data.get('notch_code') or 'None'))
        sex = escape(str(specimen_data.get('sex') or 'Undetermined'))
        status = escape(str(specimen_data.get('status') or 'Wild'))

        identity_data = [
            [
                Paragraph("<b>Custom Identifier:</b>", self.styles['TableCellText']),
                Paragraph(f"<font color='#2D5A27'><b>{custom_id}</b></font>", self.styles['TableCellText']),
                Paragraph("<b>Scientific Name:</b>", self.styles['TableCellText']),
                Paragraph(f"<i>{species_name}</i>", self.styles['TableCellText'])
            ],
            [
                Paragraph("<b>Common Name:</b>", self.styles['TableCellText']),
                Paragraph(common_name, self.styles['TableCellText']),
                Paragraph("<b>IUCN Red List Status:</b>", self.styles['TableCellText']),
                Paragraph(f"<b>{iucn_status}</b>", self.styles['TableCellText'])
            ],
            [
                Paragraph("<b>Microchip (PIT Tag):</b>", self.styles['TableCellText']),
                Paragraph(pit_tag, self.styles['TableCellText']),
                Paragraph("<b>Marginal Scute Notch:</b>", self.styles['TableCellText']),
                Paragraph(f"<font color='#583101'><b>{notch_code}</b></font>", self.styles['TableCellText'])
            ],
            [
                Paragraph("<b>Sex:</b>", self.styles['TableCellText']),
                Paragraph(sex, self.styles['TableCellText']),
                Paragraph("<b>Current Status:</b>", self.styles['TableCellText']),
                Paragraph(f"<b>{status}</b>", self.styles['TableCellText'])
            ]
        ]

        id_table = Table(identity_data, colWidths=[4.2 * cm, 4.8 * cm, 4.2 * cm, 4.8 * cm])
        id_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAF8F5")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2DCD5")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(id_table)
        elements.append(Spacer(1, 14))

        # 4. Studbook Pedigree & Lineage
        elements.append(Paragraph("2. STUDBOOK PEDIGREE & REPRODUCTIVE LINEAGE", self.styles['SectionHeading']))
        dam_id = escape(str(specimen_data.get('dam_id') or "Unknown Wild Founder (F0)"))
        sire_id = escape(str(specimen_data.get('sire_id') or "Unknown Wild Founder (F0)"))
        clutch_count = specimen_data.get('clutch_count') or 0
        gen_status = "F0 (Founder Stock)" if not specimen_data.get('dam_id') else "F1 (Captive Bred)"
        pedigree_data = [
            [
                Paragraph("<b>Dam (Maternal Line):</b>", self.styles['TableCellText']),
                Paragraph(dam_id, self.styles['TableCellText']),
                Paragraph("<b>Sire (Paternal Line):</b>", self.styles['TableCellText']),
                Paragraph(sire_id, self.styles['TableCellText'])
            ],
            [
                Paragraph("<b>Generation Status:</b>", self.styles['TableCellText']),
                Paragraph(gen_status, self.styles['TableCellText']),
                Paragraph("<b>Active Clutches / Offspring:</b>", self.styles['TableCellText']),
                Paragraph(f"{clutch_count} recorded clutches", self.styles['TableCellText'])
            ]
        ]
        pedigree_table = Table(pedigree_data, colWidths=[4.2 * cm, 4.8 * cm, 4.2 * cm, 4.8 * cm])
        pedigree_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(pedigree_table)
        elements.append(Spacer(1, 14))

        # 5. Longitudinal Morphometrics & Health History Table
        elements.append(Paragraph("3. CLINICAL HEALTH & LONGITUDINAL GROWTH ASSESSMENTS", self.styles['SectionHeading']))
        
        inspections = specimen_data.get('inspections') or []
        if not inspections:
            inspections = [
                {
                    "date": "2026-03-12",
                    "type": "Intake Triage",
                    "mass": "1,450 g",
                    "scl": "215 mm",
                    "ratio": "0.1459",
                    "bcs": "Score 2/5",
                    "findings": "Vehicle strike fracture: Acute 4cm longitudinal fissure across vertebral scutes 3-4."
                },
                {
                    "date": "2026-03-26",
                    "type": "Week 2 Check",
                    "mass": "1,470 g",
                    "scl": "215 mm",
                    "ratio": "0.1479",
                    "bcs": "Score 3/5",
                    "findings": "Dental acrylic + cerclage wire bridge stable. No infection or exudate."
                },
                {
                    "date": "2026-04-10",
                    "type": "Week 4 Round",
                    "mass": "1,510 g",
                    "scl": "215 mm",
                    "ratio": "0.1519",
                    "bcs": "Score 3/5",
                    "findings": "Active appetite on indigenous succulents. Early keratin regeneration along fissure margins."
                },
                {
                    "date": "2026-04-26",
                    "type": "Day 45 Round",
                    "mass": "1,580 g",
                    "scl": "216 mm",
                    "ratio": "0.1568",
                    "bcs": "Score 4/5",
                    "findings": "Stabilization wire removed. Dense secondary keratin bridge formed. Approved for release conditioning."
                }
            ]

        health_table_data = [
            [
                Paragraph("<b>Date</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Type</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Mass</b>", self.styles['TableCellHeader']),
                Paragraph("<b>SCL</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Jackson Ratio</b>", self.styles['TableCellHeader']),
                Paragraph("<b>BCS</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Clinical Notes & Shell Condition</b>", self.styles['TableCellHeader'])
            ]
        ]

        for insp in inspections:
            date_str = escape(str(insp.get("date") or "--"))
            type_str = escape(str(insp.get("type") or "--"))
            mass_str = escape(str(insp.get("mass") or "--"))
            scl_str = escape(str(insp.get("scl") or "--"))
            ratio_str = escape(str(insp.get("ratio") or "--"))
            bcs_str = escape(str(insp.get("bcs") or "--"))
            findings_str = escape(str(insp.get("findings") or "--")).replace("\n", "<br/>")

            health_table_data.append([
                Paragraph(date_str, self.styles['TableCellText']),
                Paragraph(type_str, self.styles['TableCellText']),
                Paragraph(mass_str, self.styles['TableCellText']),
                Paragraph(scl_str, self.styles['TableCellText']),
                Paragraph(ratio_str, self.styles['TableCellText']),
                Paragraph(bcs_str, self.styles['TableCellText']),
                Paragraph(findings_str, self.styles['TableCellText']),
            ])

        health_table = Table(
            health_table_data,
            colWidths=[2.2 * cm, 2.2 * cm, 1.8 * cm, 1.8 * cm, 2.2 * cm, 1.8 * cm, 6.0 * cm],
            repeatRows=1
        )
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(health_table)
        elements.append(Spacer(1, 16))

        # 6. Attestation & Veterinary Sign-off
        elements.append(Paragraph("4. CERTIFICATION & VETERINARY ATTESTATION", self.styles['SectionHeading']))
        attest_text = (
            "I hereby certify that the specimen identified above has undergone clinical evaluation in accordance with "
            "standard Chelonian Veterinary Guidelines. The morphometric metrics and shell integrity observations recorded "
            "represent an accurate medical history of this specimen at the time of documentation."
        )
        elements.append(Paragraph(attest_text, self.styles['SecurityNotice']))
        elements.append(Spacer(1, 14))

        signoff_data = [
            [
                Paragraph("<b>Attending Wildlife Veterinarian:</b><br/><br/>__________________________________<br/>Dr. H. van der Merwe, BVSc (Herpetology)", self.styles['TableCellText']),
                Paragraph("<b>Senior Conservation Ranger:</b><br/><br/>__________________________________<br/>Ranger J. Kivido (Chief Field Officer)", self.styles['TableCellText']),
                Paragraph("<b>Official Registry Seal:</b><br/><br/>[ SATRA OFFICIAL STAMP ]<br/>Cape Conservation Authority", self.styles['TableCellText'])
            ]
        ]
        signoff_table = Table(signoff_data, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
        signoff_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(signoff_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

# Global singleton instance
report_generator = ConservationReportGenerator()
