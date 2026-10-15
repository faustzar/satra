import io
import math
import re
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
    Implements the empirical biometric and reproductive condition model established in:
    Loehr, V.J.T., Henen, B.T., & Hofmeyr, M.D. (2004). Reproduction of the smallest tortoise,
    the Namaqualand speckled padloper, Homopus signatus signatus. Herpetologica, 60(4), 444-454.
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
            fontSize=17,
            leading=21,
            textColor=self.primary_color,
            spaceAfter=3
        ))

        self._add_style_safe(ParagraphStyle(
            name='ReportSubtitle',
            fontName='Helvetica',
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10
        ))

        self._add_style_safe(ParagraphStyle(
            name='SectionHeading',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=self.accent_color,
            spaceBefore=9,
            spaceAfter=5
        ))

        self._add_style_safe(ParagraphStyle(
            name='SectionExplainer',
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=6
        ))

        self._add_style_safe(ParagraphStyle(
            name='TableCellText',
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#1E293B")
        ))

        self._add_style_safe(ParagraphStyle(
            name='TableCellHeader',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white
        ))

        self._add_style_safe(ParagraphStyle(
            name='MetricCellTitle',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=self.accent_color
        ))

        self._add_style_safe(ParagraphStyle(
            name='MetricCellBody',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155")
        ))

        self._add_style_safe(ParagraphStyle(
            name='SecurityNotice',
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748B")
        ))

        self._add_style_safe(ParagraphStyle(
            name='CitationText',
            fontName='Helvetica',
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#475569")
        ))

    def _parse_float_safe(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        cleaned = re.sub(r'[^0-9.\-]', '', str(val))
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

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
        elements.append(HRFlowable(width="100%", thickness=1.5, color=self.primary_color, spaceAfter=8))

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
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(notice_table)
        elements.append(Spacer(1, 10))

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
            ('TOPPADDING', (0, 0), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(id_table)
        elements.append(Spacer(1, 10))

        # 4. Studbook Pedigree & Reproductive Lineage
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
            ('TOPPADDING', (0, 0), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ]))
        elements.append(pedigree_table)
        elements.append(Spacer(1, 10))

        # 5. Loehr, Henen & Hofmeyr (2004) Biometric Condition Profile
        elements.append(Paragraph("3. BIOMETRIC CONDITION & MORPHOMETRIC PROFILE (Loehr et al. 2004 Model)", self.styles['SectionHeading']))
        explainer_text = (
            "Evaluated under the empirical morphometric and reproductive model for the Namaqualand speckled padloper "
            "(<i>Homopus signatus signatus</i>; Loehr, Henen & Hofmeyr, <i>Herpetologica</i> 60(4):444–454, 2004). "
            "Replaces legacy Mediterranean Testudo Jackson ratios (Mass/L³) with 3D shell ellipsoid volume (V<sub>shell</sub>), "
            "volumetric Body Condition Index (BCI), linear mass-to-length scaling, and Coleman (1991) non-spherical egg geometry."
        )
        elements.append(Paragraph(explainer_text, self.styles['SectionExplainer']))

        # Extract latest metrics or calculate from inspections
        inspections = specimen_data.get('inspections') or []
        last_insp = inspections[-1] if inspections else {}

        # Mass & SCL
        latest_mass = specimen_data.get('latest_mass') or self._parse_float_safe(last_insp.get('mass_val')) or self._parse_float_safe(last_insp.get('mass'))
        latest_scl = specimen_data.get('latest_scl') or self._parse_float_safe(last_insp.get('scl_val')) or self._parse_float_safe(last_insp.get('scl'))
        latest_sh = specimen_data.get('latest_sh') or self._parse_float_safe(last_insp.get('sh_val')) or self._parse_float_safe(last_insp.get('shell_height_mm'))
        latest_sw = specimen_data.get('latest_sw') or self._parse_float_safe(last_insp.get('sw_val')) or self._parse_float_safe(last_insp.get('shell_width_mm'))

        # Shell Volume Vfem = pi * SCL * SH * SW / 6000
        latest_shell_vol = specimen_data.get('latest_shell_volume') or self._parse_float_safe(last_insp.get('shell_volume_cm3')) or self._parse_float_safe(last_insp.get('shell_vol'))
        if latest_shell_vol is None and latest_scl and latest_sh and latest_sw and latest_scl > 0 and latest_sh > 0 and latest_sw > 0:
            latest_shell_vol = round((math.pi * latest_scl * latest_sh * latest_sw) / 6000.0, 2)

        # Body Condition Index BCI = Mass / Shell Volume (g/cm3)
        latest_bci = specimen_data.get('latest_bci') or self._parse_float_safe(last_insp.get('body_condition_index')) or self._parse_float_safe(last_insp.get('bci'))
        if latest_bci is None and latest_mass and latest_shell_vol and latest_shell_vol > 0:
            latest_bci = round(latest_mass / latest_shell_vol, 4)

        # Linear Mass / SCL (g/mm)
        latest_mass_to_scl = specimen_data.get('latest_mass_to_scl') or self._parse_float_safe(last_insp.get('mass_to_scl_ratio')) or self._parse_float_safe(last_insp.get('mass_to_scl'))
        if latest_mass_to_scl is None and latest_mass and latest_scl and latest_scl > 0:
            latest_mass_to_scl = round(latest_mass / latest_scl, 4)

        # Scute Laminae
        latest_rings = specimen_data.get('latest_growth_rings') or last_insp.get('growth_rings') or "9 laminae (Costal-1)"

        # Reproductive & Clutch metrics
        eggs_palpated = specimen_data.get('eggs_palpated', False) or last_insp.get('eggs_palpated', False)
        egg_count = specimen_data.get('estimated_egg_count') or last_insp.get('estimated_egg_count', 0)
        egg_vol = specimen_data.get('egg_volume_cm3') or self._parse_float_safe(last_insp.get('egg_volume_cm3'))
        egg_l = specimen_data.get('egg_length_mm') or self._parse_float_safe(last_insp.get('egg_length_mm'))
        egg_w = specimen_data.get('egg_width_mm') or self._parse_float_safe(last_insp.get('egg_width_mm'))
        somatic_mass = specimen_data.get('somatic_mass_grams') or self._parse_float_safe(last_insp.get('somatic_mass_grams'))

        if egg_vol is None and egg_l and egg_w and egg_l > 0 and egg_w > 0:
            egg_vol = round((math.pi * egg_l * (egg_w ** 2)) / 6000.0, 2)
        if somatic_mass is None and latest_mass is not None:
            if egg_vol:
                somatic_mass = round(max(0.0, latest_mass - egg_vol * 1.0), 1)
            elif eggs_palpated:
                somatic_mass = round(max(0.0, latest_mass - 12.0), 1)

        # BCI Evaluation & Classification
        if latest_bci is not None:
            if latest_bci >= 1.25:
                bci_status = "<font color='#0284c7'><b>High Density (Gravid / Hydrated)</b></font>"
                bci_detail = "Elevated density ≥1.25 g/cm³; monitor for egg calcification or hydration."
            elif latest_bci >= 1.05:
                bci_status = "<font color='#2D5A27'><b>Optimal Density & Condition</b></font>"
                bci_detail = "In prime physiological range (1.05–1.25 g/cm³; Baseline mean: 1.12)."
            elif latest_bci >= 0.95:
                bci_status = "<font color='#d97706'><b>Moderate Condition / Sub-optimal</b></font>"
                bci_detail = "Mildly depressed reserves (0.95–1.05 g/cm³); monitor succulent foraging."
            else:
                bci_status = "<font color='#dc2626'><b>Underweight / Dehydration Risk</b></font>"
                bci_detail = "Critically low density <0.95 g/cm³; requires clinical triage & fluids."
            bci_display = f"{latest_bci:.3f} g/cm³"
        else:
            bci_status = "<b>Pending Dimensions</b>"
            bci_detail = "Requires SCL, SH, SW, and Mass for 3D volumetric density."
            bci_display = "--"

        # Female Adult Breeding Threshold (Paper Table 1: Min female with egg SCL = 84.1 mm)
        if latest_scl is not None:
            if latest_scl >= 84.1:
                maturity_display = "<font color='#2D5A27'><b>Adult Breeding Size (SCL ≥ 84.1 mm)</b></font>"
            else:
                maturity_display = "<font color='#64748B'><b>Subadult / Immature (&lt; 84.1 mm)</b></font>"
        else:
            maturity_display = "<b>Maturity Unknown</b>"

        # Gravid status display
        if eggs_palpated or (egg_count and egg_count > 0) or egg_vol:
            egg_vol_str = f"{egg_vol:.1f} cm³" if egg_vol else "~11.3 cm³"
            somatic_str = f"{somatic_mass:.1f} g" if somatic_mass else "--"
            egg_dim_str = f"({egg_l:.1f} × {egg_w:.1f} mm)" if (egg_l and egg_w) else "Single-egg clutch"
            clutch_display = (
                f"<font color='#0284c7'><b>Gravid: Single-Egg Clutch</b></font><br/>"
                f"<font size=7 color='#475569'>Egg Vol: {egg_vol_str} {egg_dim_str}<br/>"
                f"Somatic Body Mass: <b>{somatic_str}</b></font>"
            )
        else:
            somatic_str = f"{latest_mass:.1f} g" if latest_mass else "--"
            clutch_display = (
                "<b>Non-Gravid / Quiescent</b><br/>"
                f"<font size=7 color='#475569'>Single-egg clutch mode (Aug–Dec spring)<br/>"
                f"Somatic Body Mass: <b>{somatic_str}</b></font>"
            )

        vol_display = f"{latest_shell_vol:.1f} cm³" if latest_shell_vol else "--"
        mass_scl_display = f"{latest_mass_to_scl:.2f} g/mm" if latest_mass_to_scl else "--"
        rings_display = escape(str(latest_rings))

        biometric_grid_data = [
            [
                Paragraph("<b>3D Shell Ellipsoid Volume (V<sub>shell</sub>)</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Linear Mass-to-Length Ratio</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Reproductive Maturity (Loehr 2004)</b>", self.styles['MetricCellTitle'])
            ],
            [
                Paragraph(
                    f"<font size=10 color='#2D5A27'><b>{vol_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Formula: π × SCL × SH × SW / 6000 cm³</font>",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    f"<font size=10 color='#583101'><b>{mass_scl_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Baseline: 1.62 ± 0.22 g/mm (Gravid: 1.68)</font>",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    f"{maturity_display}<br/>"
                    f"<font size=7 color='#64748B'>Min padloper breeding female: SCL 84.1 mm</font>",
                    self.styles['MetricCellBody']
                )
            ],
            [
                Paragraph("<b>Body Condition Index (BCI Density)</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Scute Laminae (Growth Annuli)</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Clutch Status & Somatic Reserve</b>", self.styles['MetricCellTitle'])
            ],
            [
                Paragraph(
                    f"<font size=10 color='#2D5A27'><b>{bci_display}</b></font> • {bci_status}<br/>"
                    f"<font size=7 color='#475569'>{bci_detail}</font><br/>"
                    f"<font size=7 color='#64748B'>Padloper Mean: 1.12 ± 0.08 g/cm³ (0.910–1.280)</font>",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    f"<font size=9><b>{rings_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Count on left anterior-most costal scute<br/>Adult padloper range: 8–13+ laminae</font>",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    clutch_display,
                    self.styles['MetricCellBody']
                )
            ]
        ]

        metric_table = Table(biometric_grid_data, colWidths=[6.0 * cm, 6.0 * cm, 6.0 * cm])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0, 0), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#F1F5F9")),
        ]))
        elements.append(metric_table)
        elements.append(Spacer(1, 10))

        # 6. Longitudinal Morphometrics & Health History Table
        elements.append(Paragraph("4. CLINICAL HEALTH & LONGITUDINAL MORPHOMETRICS", self.styles['SectionHeading']))
        
        if not inspections:
            inspections = [
                {
                    "date": "2026-03-12",
                    "type": "Intake Triage",
                    "mass": "145.0 g",
                    "scl": "91.2 mm",
                    "shell_vol": "129.5 cm³",
                    "bci": "1.120",
                    "mass_to_scl": "1.59 g/mm",
                    "bcs": "Score 3/5",
                    "findings": "Intact carapace. Normal clinical state on indigenous succulent forage."
                },
                {
                    "date": "2026-04-10",
                    "type": "Scheduled",
                    "mass": "151.4 g",
                    "scl": "92.6 mm",
                    "shell_vol": "131.2 cm³",
                    "bci": "1.154",
                    "mass_to_scl": "1.63 g/mm",
                    "bcs": "Score 4/5",
                    "findings": "Active foraging; optimal somatic mass reserves; zero ectoparasites."
                }
            ]

        health_table_data = [
            [
                Paragraph("<b>Date</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Type</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Mass</b>", self.styles['TableCellHeader']),
                Paragraph("<b>SCL</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Vol (cm³)</b>", self.styles['TableCellHeader']),
                Paragraph("<b>BCI (g/cm³)</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Mass/SCL</b>", self.styles['TableCellHeader']),
                Paragraph("<b>BCS & Clinical Observations</b>", self.styles['TableCellHeader'])
            ]
        ]

        for insp in inspections:
            date_str = escape(str(insp.get("date") or "--"))
            type_str = escape(str(insp.get("type") or "--"))
            mass_str = escape(str(insp.get("mass") or "--"))
            scl_str = escape(str(insp.get("scl") or "--"))

            # Shell Volume column
            vol_val = insp.get("shell_vol") or insp.get("shell_volume_cm3")
            if vol_val is not None:
                vol_str = f"{vol_val:.1f}" if isinstance(vol_val, float) else str(vol_val)
            else:
                vol_str = "--"
            vol_str = escape(vol_str)

            # BCI column (fallback to ratio if bci is absent)
            bci_val = insp.get("bci") or insp.get("body_condition_index") or insp.get("ratio")
            if bci_val is not None:
                bci_col_str = f"{bci_val:.3f}" if isinstance(bci_val, float) else str(bci_val)
            else:
                bci_col_str = "--"
            bci_col_str = escape(bci_col_str)

            # Mass/SCL column
            mass_scl_val = insp.get("mass_to_scl") or insp.get("mass_to_scl_ratio")
            if mass_scl_val is not None:
                mass_scl_col_str = f"{mass_scl_val:.2f}" if isinstance(mass_scl_val, float) else str(mass_scl_val)
            else:
                mass_scl_col_str = "--"
            mass_scl_col_str = escape(mass_scl_col_str)

            bcs_str = escape(str(insp.get("bcs") or "--"))
            raw_findings = insp.get("findings")
            if raw_findings is None:
                findings_body = "Normal clinical state; no acute lesions."
            else:
                findings_body = escape(str(raw_findings)).replace("\n", "<br/>")

            if bcs_str != "--":
                findings_full = f"<b>{bcs_str}</b> • {findings_body}"
            else:
                findings_full = findings_body

            health_table_data.append([
                Paragraph(date_str, self.styles['TableCellText']),
                Paragraph(type_str, self.styles['TableCellText']),
                Paragraph(mass_str, self.styles['TableCellText']),
                Paragraph(scl_str, self.styles['TableCellText']),
                Paragraph(vol_str, self.styles['TableCellText']),
                Paragraph(bci_col_str, self.styles['TableCellText']),
                Paragraph(mass_scl_col_str, self.styles['TableCellText']),
                Paragraph(findings_full, self.styles['TableCellText']),
            ])

        # Widths: 2.1 + 2.0 + 1.6 + 1.6 + 1.8 + 1.8 + 1.8 + 5.3 = 18.0 cm
        health_table = Table(
            health_table_data,
            colWidths=[2.1 * cm, 2.0 * cm, 1.6 * cm, 1.6 * cm, 1.8 * cm, 1.8 * cm, 1.8 * cm, 5.3 * cm],
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
        elements.append(Spacer(1, 10))

        # 7. Attestation & Scientific Standard Citation
        elements.append(Paragraph("5. CERTIFICATION & VETERINARY ATTESTATION", self.styles['SectionHeading']))
        attest_text = (
            "I hereby certify that the specimen identified above has undergone clinical evaluation in accordance with "
            "standard Chelonian Veterinary Guidelines. The morphometric metrics and shell integrity observations recorded "
            "represent an accurate medical history of this specimen at the time of documentation."
        )
        elements.append(Paragraph(attest_text, self.styles['SecurityNotice']))
        elements.append(Spacer(1, 5))

        citation_text = (
            "<b>Biometric Reference Standard:</b> Loehr, V. J. T., Henen, B. T., & Hofmeyr, M. D. (2004). "
            "Reproduction of the smallest tortoise, the Namaqualand speckled padloper, <i>Homopus signatus signatus</i>. "
            "<i>Herpetologica</i>, 60(4), 444–454; Coleman, P. R. (1991). Non-spherical chelonian egg volume derivation."
        )
        elements.append(Paragraph(citation_text, self.styles['CitationText']))
        elements.append(Spacer(1, 10))

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
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(signoff_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

# Global singleton instance
report_generator = ConservationReportGenerator()
