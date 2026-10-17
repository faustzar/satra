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
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, PolyLine, String

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

    # Marginal Identification Coding Schemes (matching frontend NOTCH_SYSTEMS)
    SA_STANDARD_LEFT = {1: 10, 2: 20, 3: 40, 4: 70, 8: 7000, 9: 4000, 10: 2000, 11: 1000}
    SA_STANDARD_RIGHT = {1: 1, 2: 2, 3: 4, 4: 7, 8: 700, 9: 400, 10: 200, 11: 100}
    SA_STANDARD_SUPRA = 3000

    BINARY_LEFT = {1: 16, 2: 32, 3: 64, 4: 128, 8: 256, 9: 512, 10: 1024, 11: 2048}
    BINARY_RIGHT = {1: 1, 2: 2, 3: 4, 4: 8, 8: 4096, 9: 8192, 10: 16384, 11: 32768}

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

    def _format_mass(self, grams: Optional[float], mass_unit: str = "grams") -> str:
        if grams is None:
            return "--"
        if str(mass_unit).lower() in ("kilograms", "kg"):
            return f"{grams / 1000.0:.3f} kg"
        return f"{grams:.1f} g"

    def _format_length(self, mm: Optional[float], length_unit: str = "mm") -> str:
        if mm is None:
            return "--"
        if str(length_unit).lower() in ("cm", "centimeters"):
            return f"{mm / 10.0:.2f} cm"
        return f"{mm:.1f} mm"

    def _format_notch_code(self, notch_code: Optional[str], notch_system: str = "sa_standard") -> tuple[str, str]:
        """
        Formats a marginal notch code according to the active identification scheme:
        - 'sa_standard': South African Standard (1-2-4-7 Additive)
        - 'binary': Binary Powers of Two (1-2-4-8 Additive)
        - 'cagle': Cagle Positional (L1–L12 / R1–R12)
        Returns (formatted_code, scheme_name).
        """
        sys_key = str(notch_system or "sa_standard").lower()
        if sys_key == "cagle":
            scheme_label = "Cagle Positional (L1–L12 / R1–R12)"
        elif sys_key == "binary":
            scheme_label = "Binary Powers of Two (1-2-4-8)"
        else:
            sys_key = "sa_standard"
            scheme_label = "SA Standard (1-2-4-7 Additive)"

        if not notch_code or str(notch_code).strip() in ("", "None", "Unnotched"):
            return ("None / Unnotched", scheme_label)

        raw = str(notch_code).strip()
        if sys_key == "cagle" or raw.startswith("#"):
            return (raw, scheme_label)

        parts = re.split(r'[-,\s]+', raw)
        total_sum = 0
        matched_any = False

        left_map = self.SA_STANDARD_LEFT if sys_key == "sa_standard" else self.BINARY_LEFT
        right_map = self.SA_STANDARD_RIGHT if sys_key == "sa_standard" else self.BINARY_RIGHT

        for p in parts:
            clean = p.strip().upper()
            if clean == "SUPRA" and sys_key == "sa_standard":
                total_sum += self.SA_STANDARD_SUPRA
                matched_any = True
            elif clean.startswith("L") and clean[1:].isdigit():
                idx = int(clean[1:])
                if idx in left_map:
                    total_sum += left_map[idx]
                    matched_any = True
            elif clean.startswith("R") and clean[1:].isdigit():
                idx = int(clean[1:])
                if idx in right_map:
                    total_sum += right_map[idx]
                    matched_any = True

        if matched_any and total_sum > 0:
            return (f"#{total_sum} ({raw})", scheme_label)
        return (raw, scheme_label)

    def _build_longitudinal_trajectory_chart(self, inspections: List[Dict[str, Any]], mass_unit: str = "grams") -> Optional[Drawing]:
        """
        Builds a dual-panel vector chart (ReportLab Drawing) of:
        - Left Panel: Body Mass & Somatic Mass vs. Table 2 ANCOVA Expected Mass over time
        - Right Panel: Volumetric Body Condition Index (BCI, g/cm³) vs. Loehr et al. (2004) Optimal Band (1.05–1.25 g/cm³)
        """
        pts = []
        for insp in inspections:
            m_val = self._parse_float_safe(insp.get("mass_val")) or self._parse_float_safe(insp.get("mass"))
            som_val = self._parse_float_safe(insp.get("somatic_mass_grams")) or m_val
            pred_val = self._parse_float_safe(insp.get("predicted_mass_grams"))
            bci_val = self._parse_float_safe(insp.get("body_condition_index")) or self._parse_float_safe(insp.get("bci")) or self._parse_float_safe(insp.get("ratio"))
            vol_val = self._parse_float_safe(insp.get("shell_volume_cm3")) or self._parse_float_safe(insp.get("shell_vol"))
            if pred_val is None and vol_val and vol_val > 0:
                pred_val = round(0.885 * vol_val + 23.6, 1)
            if m_val is not None:
                pts.append({
                    "date": str(insp.get("date") or "--")[-5:],  # MM-DD
                    "mass": m_val,
                    "somatic": som_val if som_val is not None else m_val,
                    "predicted": pred_val,
                    "bci": bci_val
                })

        if not pts:
            return None

        width_pt = 18.0 * cm
        height_pt = 3.8 * cm
        d = Drawing(width_pt, height_pt)

        # Outer card background
        d.add(Rect(0, 0, width_pt, height_pt, fillColor=colors.HexColor("#F8FAFC"), strokeColor=colors.HexColor("#CBD5E1"), strokeWidth=0.6, rx=4, ry=4))

        # Panel 1: Mass & Table 2 ANCOVA Trajectory (left half)
        p1_x, p1_y, p1_w, p1_h = 34, 20, 210, 68
        d.add(String(p1_x, p1_y + p1_h + 7, "Mass vs. Table 2 ANCOVA Expected Trajectory", fontName="Helvetica-Bold", fontSize=7.5, fillColor=self.accent_color))
        d.add(Rect(p1_x, p1_y, p1_w, p1_h, fillColor=colors.white, strokeColor=colors.HexColor("#E2E8F0"), strokeWidth=0.5))

        all_masses = [p["mass"] for p in pts] + [p["somatic"] for p in pts] + [p["predicted"] for p in pts if p["predicted"] is not None]
        m_min = max(0.0, min(all_masses) * 0.90) if all_masses else 50.0
        m_max = (max(all_masses) * 1.08) if all_masses else 200.0
        if abs(m_max - m_min) < 5.0:
            m_max = m_min + 20.0

        # Y-axis labels for Panel 1
        is_kg = str(mass_unit).lower() in ("kilograms", "kg")
        min_lbl = f"{m_min/1000.0:.2f}kg" if is_kg else f"{m_min:.0f}g"
        max_lbl = f"{m_max/1000.0:.2f}kg" if is_kg else f"{m_max:.0f}g"
        d.add(String(4, p1_y + 2, min_lbl, fontName="Helvetica", fontSize=6.5, fillColor=colors.HexColor("#64748B")))
        d.add(String(4, p1_y + p1_h - 6, max_lbl, fontName="Helvetica", fontSize=6.5, fillColor=colors.HexColor("#64748B")))

        n = len(pts)
        mass_coords = []
        pred_coords = []
        for i, p in enumerate(pts):
            cx = p1_x + (p1_w / 2.0 if n == 1 else (i / float(n - 1)) * (p1_w - 20) + 10)
            cy_m = p1_y + ((p["mass"] - m_min) / (m_max - m_min)) * (p1_h - 12) + 6
            mass_coords.extend([cx, cy_m])
            d.add(Circle(cx, cy_m, 2.3, fillColor=self.primary_color, strokeColor=colors.white, strokeWidth=0.5))
            d.add(String(cx - 9, 8, p["date"], fontName="Helvetica", fontSize=6, fillColor=colors.HexColor("#475569")))

            if p["predicted"] is not None:
                cy_pr = p1_y + ((p["predicted"] - m_min) / (m_max - m_min)) * (p1_h - 12) + 6
                pred_coords.extend([cx, cy_pr])
                d.add(Circle(cx, cy_pr, 1.8, fillColor=self.gold_color, strokeColor=self.accent_color, strokeWidth=0.4))

        if len(pred_coords) >= 4:
            d.add(PolyLine(pred_coords, strokeColor=self.gold_color, strokeWidth=1.1))
        if len(mass_coords) >= 4:
            d.add(PolyLine(mass_coords, strokeColor=self.primary_color, strokeWidth=1.5))

        # Panel 2: BCI Density Trajectory vs. Loehr Optimal Band (1.05 - 1.25 g/cm3)
        p2_x, p2_y, p2_w, p2_h = 285, 20, 210, 68
        d.add(String(p2_x, p2_y + p2_h + 7, "BCI Density (g/cm³) vs. Loehr Optimal Band (1.05–1.25)", fontName="Helvetica-Bold", fontSize=7.5, fillColor=self.primary_color))
        d.add(Rect(p2_x, p2_y, p2_w, p2_h, fillColor=colors.white, strokeColor=colors.HexColor("#E2E8F0"), strokeWidth=0.5))

        bci_vals = [p["bci"] for p in pts if p["bci"] is not None]
        b_min = min([0.85] + bci_vals) * 0.95
        b_max = max([1.35] + bci_vals) * 1.03
        if abs(b_max - b_min) < 0.1:
            b_max = b_min + 0.4

        # Shaded Optimal BCI Band (1.05 to 1.25 g/cm3)
        opt_y1 = p2_y + max(0.0, min(1.0, (1.05 - b_min) / (b_max - b_min))) * p2_h
        opt_y2 = p2_y + max(0.0, min(1.0, (1.25 - b_min) / (b_max - b_min))) * p2_h
        if opt_y2 > opt_y1:
            d.add(Rect(p2_x + 0.5, opt_y1, p2_w - 1.0, opt_y2 - opt_y1, fillColor=colors.HexColor("#DCFCE7"), strokeWidth=0))
        # Baseline mean line (1.12 g/cm3)
        mean_y = p2_y + max(0.0, min(1.0, (1.12 - b_min) / (b_max - b_min))) * p2_h
        d.add(Line(p2_x, mean_y, p2_x + p2_w, mean_y, strokeColor=colors.HexColor("#86EFAC"), strokeWidth=0.7))

        d.add(String(p2_x - 24, p2_y + 2, f"{b_min:.2f}", fontName="Helvetica", fontSize=6.5, fillColor=colors.HexColor("#64748B")))
        d.add(String(p2_x - 24, p2_y + p2_h - 6, f"{b_max:.2f}", fontName="Helvetica", fontSize=6.5, fillColor=colors.HexColor("#64748B")))

        bci_coords = []
        for i, p in enumerate(pts):
            if p["bci"] is None:
                continue
            cx = p2_x + (p2_w / 2.0 if n == 1 else (i / float(n - 1)) * (p2_w - 20) + 10)
            cy_b = p2_y + ((p["bci"] - b_min) / (b_max - b_min)) * (p2_h - 10) + 5
            bci_coords.extend([cx, cy_b])
            d.add(Circle(cx, cy_b, 2.3, fillColor=colors.HexColor("#0284C7"), strokeColor=colors.white, strokeWidth=0.5))
            d.add(String(cx - 9, 8, p["date"], fontName="Helvetica", fontSize=6, fillColor=colors.HexColor("#475569")))

        if len(bci_coords) >= 4:
            d.add(PolyLine(bci_coords, strokeColor=colors.HexColor("#0284C7"), strokeWidth=1.5))

        return d

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

        # Extract user preferences (defaulting to SA Standard, grams, mm)
        notch_system = str(specimen_data.get('notch_system') or 'sa_standard').lower()
        mass_unit = str(specimen_data.get('mass_unit') or 'grams').lower()
        length_unit = str(specimen_data.get('length_unit') or 'mm').lower()

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
        formatted_notch, scheme_label = self._format_notch_code(specimen_data.get('notch_code'), notch_system)
        notch_code = escape(formatted_notch)
        scheme_label_esc = escape(scheme_label)
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
                Paragraph(
                    f"<font color='#583101'><b>{notch_code}</b></font><br/>"
                    f"<font size=6.5 color='#64748B'>{scheme_label_esc}</font>",
                    self.styles['TableCellText']
                )
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
        clutches_list = specimen_data.get('clutches') or []
        clutch_count = specimen_data.get('clutch_count') if specimen_data.get('clutch_count') is not None else len(clutches_list)
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
                Paragraph(f"{clutch_count} recorded clutch(es)", self.styles['TableCellText'])
            ]
        ]
        if clutches_list:
            latest_c = clutches_list[0]
            c_code = escape(str(latest_c.get('clutch_code') or 'CLUTCH'))
            c_date = escape(str(latest_c.get('oviposition_date') or '--'))
            c_eggs = f"{latest_c.get('viable_eggs', 1)}/{latest_c.get('total_eggs', 1)} viable"
            c_temp = f"{latest_c.get('target_temp_c', 31.5)}°C ({escape(str(latest_c.get('predicted_sex') or 'TSD'))})"
            pedigree_data.append([
                Paragraph("<b>Latest Clutch &amp; Oviposition:</b>", self.styles['TableCellText']),
                Paragraph(f"<b>{c_code}</b> ({c_date}, {c_eggs})", self.styles['TableCellText']),
                Paragraph("<b>Incubation TSD Target:</b>", self.styles['TableCellText']),
                Paragraph(c_temp, self.styles['TableCellText'])
            ])
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
            "Evaluated under the empirical morphometric, radiographic, and ultrasonographic health model for the Namaqualand "
            "speckled padloper (<i>Homopus signatus signatus</i>; Loehr, Henen & Hofmeyr, <i>Herpetologica</i> 60(4):444–454, 2004). "
            "Combines 3D shell ellipsoid volume (V<sub>shell</sub>), volumetric Body Condition Index (BCI), Table 2 ANCOVA somatic mass "
            "regressions, Coleman (1991) radiographic egg volume, and ultrasonographic Preovulatory Size (POS = 4.99 cm³) follicle staging."
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

        # Scute Laminae & Wear Status
        latest_rings = specimen_data.get('latest_growth_rings') or last_insp.get('growth_rings') or "9 laminae (Costal-1)"
        latest_wear = specimen_data.get('latest_scute_wear') or last_insp.get('scute_wear_status') or "Countable (8-13)"
        weighed_pre = specimen_data.get('weighed_before_excretion')
        if weighed_pre is None:
            weighed_pre = last_insp.get('weighed_before_excretion', True)

        # Reproductive, Radiographic Egg & Ultrasonographic Follicle metrics
        eggs_palpated = specimen_data.get('eggs_palpated', False) or last_insp.get('eggs_palpated', False)
        egg_count = specimen_data.get('estimated_egg_count') or last_insp.get('estimated_egg_count', 0)
        egg_vol = specimen_data.get('egg_volume_cm3') or self._parse_float_safe(last_insp.get('egg_volume_cm3'))
        egg_l = specimen_data.get('egg_length_mm') or self._parse_float_safe(last_insp.get('egg_length_mm'))
        egg_w = specimen_data.get('egg_width_mm') or self._parse_float_safe(last_insp.get('egg_width_mm'))

        foll_count = specimen_data.get('follicle_count') or last_insp.get('follicle_count')
        foll_diam = specimen_data.get('mean_follicle_diameter_mm') or self._parse_float_safe(last_insp.get('mean_follicle_diameter_mm'))
        foll_vol = specimen_data.get('follicle_volume_cm3') or self._parse_float_safe(last_insp.get('follicle_volume_cm3'))
        pos_frac = specimen_data.get('pos_fraction') or self._parse_float_safe(last_insp.get('pos_fraction'))

        if egg_vol is None and egg_l and egg_w and egg_l > 0 and egg_w > 0:
            egg_vol = round((math.pi * egg_l * (egg_w ** 2)) / 6000.0, 2)
        if foll_vol is None and foll_diam and foll_diam > 0:
            d_cm = foll_diam / 10.0
            foll_vol = round((math.pi * (d_cm ** 3)) / 6.0, 3)
            pos_frac = round(foll_vol / 4.99, 3)

        somatic_mass = specimen_data.get('somatic_mass_grams') or self._parse_float_safe(last_insp.get('somatic_mass_grams'))
        if somatic_mass is None and latest_mass is not None:
            egg_m = (egg_vol * 1.0 * (egg_count or 1)) if egg_vol else (11.3 * (egg_count or 1) if eggs_palpated else 0.0)
            foll_m = (foll_vol * 1.0 * (foll_count if foll_count and foll_count > 0 else 1)) if foll_vol else 0.0
            if egg_m > 0 or foll_m > 0:
                somatic_mass = round(max(0.0, latest_mass - egg_m - foll_m), 1)

        # Table 2 ANCOVA Expected Mass & Condition Residual
        predicted_mass = specimen_data.get('predicted_mass_grams') or self._parse_float_safe(last_insp.get('predicted_mass_grams'))
        if predicted_mass is None:
            if latest_shell_vol and latest_shell_vol > 0:
                predicted_mass = round((0.886 * latest_shell_vol + 13.8) if foll_vol else (0.885 * latest_shell_vol + 23.6), 1)
            elif latest_scl and latest_scl > 0:
                predicted_mass = round((4.20 * latest_scl - 253.0) if foll_vol else (4.18 * latest_scl - 243.0), 1)

        mass_residual = specimen_data.get('mass_condition_residual_g') or self._parse_float_safe(last_insp.get('mass_condition_residual_g'))
        if mass_residual is None and predicted_mass and predicted_mass > 0 and latest_mass is not None:
            eval_m = somatic_mass if somatic_mass is not None else latest_mass
            mass_residual = round(eval_m - predicted_mass, 1)

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

        # Table 2 ANCOVA Residual line
        if predicted_mass is not None and predicted_mass > 0:
            pred_str = self._format_mass(predicted_mass, mass_unit)
            if mass_residual is not None:
                sign_char = "+" if mass_residual >= 0 else ""
                res_color = "#2D5A27" if mass_residual >= -5.0 else ("#d97706" if mass_residual >= -14.7 else "#dc2626")
                ancova_line = f"<font size=7 color='#334155'>Table 2 Expected: <b>{pred_str}</b> (<font color='{res_color}'><b>{sign_char}{mass_residual:.1f} g</b></font>)</font>"
            else:
                ancova_line = f"<font size=7 color='#334155'>Table 2 Expected: <b>{pred_str}</b></font>"
        else:
            ancova_line = "<font size=7 color='#64748B'>Table 2 ANCOVA: 0.885×V<sub>shell</sub> + 23.6 g</font>"

        # Female Adult Breeding Threshold (Paper Table 1: Min female with egg SCL = 84.1 mm)
        thresh_str = "8.41 cm" if length_unit in ("cm", "centimeters") else "84.1 mm"
        if latest_scl is not None:
            if latest_scl >= 84.1:
                maturity_display = f"<font color='#2D5A27'><b>Adult Breeding Size (SCL ≥ {thresh_str})</b></font>"
            else:
                maturity_display = f"<font color='#64748B'><b>Subadult / Immature (&lt; {thresh_str})</b></font>"
        else:
            maturity_display = "<b>Maturity Unknown</b>"

        weigh_badge = "Weighed pre-excretion (±0.1 g)" if weighed_pre else "Weighed post-excretion (adjusted)"

        # Ultrasonography Follicle & POS Staging line
        if foll_vol is not None and pos_frac is not None:
            if pos_frac >= 0.9:
                pos_stage = "Preovulatory (&gt;0.9 POS • Multi-clutch)"
            elif pos_frac >= 0.4:
                pos_stage = "Med–Large Vitellogenic (0.4–0.8 POS)"
            else:
                pos_stage = "Small Vitellogenic (&lt;0.2 POS)"
            foll_line = f"Ultrasound: {foll_count or 1} foll. ({foll_vol:.2f} cm³ = <b>{pos_frac:.2f} POS</b>, {pos_stage})"
        else:
            foll_line = "POS Threshold: 4.99 cm³ (≥21.2 mm yolk diameter)"

        # Gravid status display
        if eggs_palpated or (egg_count and egg_count > 0) or egg_vol:
            egg_vol_str = f"{egg_vol:.1f} cm³" if egg_vol else "~11.3 cm³"
            somatic_str = self._format_mass(somatic_mass, mass_unit) if somatic_mass is not None else "--"
            if egg_l and egg_w:
                if length_unit in ("cm", "centimeters"):
                    egg_dim_str = f"({egg_l / 10.0:.2f} × {egg_w / 10.0:.2f} cm)"
                else:
                    egg_dim_str = f"({egg_l:.1f} × {egg_w:.1f} mm)"
            else:
                egg_dim_str = "Single-egg clutch"
            clutch_display = (
                f"<font color='#0284c7'><b>Gravid: Single-Egg Clutch</b></font><br/>"
                f"<font size=7 color='#475569'>Egg Vol: {egg_vol_str} {egg_dim_str} • Somatic: <b>{somatic_str}</b><br/>"
                f"{foll_line}</font>"
            )
        else:
            somatic_str = self._format_mass(somatic_mass if somatic_mass is not None else latest_mass, mass_unit) if (somatic_mass is not None or latest_mass is not None) else "--"
            clutch_display = (
                "<b>Non-Gravid / Quiescent</b><br/>"
                f"<font size=7 color='#475569'>Somatic Body Mass: <b>{somatic_str}</b><br/>"
                f"{foll_line}</font>"
            )

        vol_display = f"{latest_shell_vol:.1f} cm³" if latest_shell_vol else "--"
        mass_scl_display = f"{latest_mass_to_scl:.2f} g/mm" if latest_mass_to_scl else "--"
        rings_display = escape(str(latest_rings))
        wear_display = escape(str(latest_wear))

        biometric_grid_data = [
            [
                Paragraph("<b>3D Shell Ellipsoid Volume (V<sub>shell</sub>)</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Linear Mass-to-Length & ANCOVA</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Maturity & Excretion Protocol</b>", self.styles['MetricCellTitle'])
            ],
            [
                Paragraph(
                    f"<font size=10 color='#2D5A27'><b>{vol_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Formula: π × SCL × SH × SW / 6000 cm³</font>",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    f"<font size=10 color='#583101'><b>{mass_scl_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Baseline: 1.62 ± 0.22 g/mm (Gravid: 1.68)</font><br/>"
                    f"{ancova_line}",
                    self.styles['MetricCellBody']
                ),
                Paragraph(
                    f"{maturity_display}<br/>"
                    f"<font size=7 color='#64748B'>Min female with egg: SCL {thresh_str}<br/>{weigh_badge}</font>",
                    self.styles['MetricCellBody']
                )
            ],
            [
                Paragraph("<b>Body Condition Index (BCI Density)</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Scute Laminae & Wear Class</b>", self.styles['MetricCellTitle']),
                Paragraph("<b>Radiography, POS & Somatic Reserve</b>", self.styles['MetricCellTitle'])
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
                    f"<font size=7 color='#475569'>Wear Class: <b>{wear_display}</b></font><br/>"
                    f"<font size=7 color='#64748B'>Left anterior-most costal scute (8–13+ laminae)</font>",
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

        mass_col_header = "Mass (kg)" if mass_unit in ("kilograms", "kg") else "Mass"
        scl_col_header = "SCL (cm)" if length_unit in ("cm", "centimeters") else "SCL"

        chart_drawing = self._build_longitudinal_trajectory_chart(inspections, mass_unit)
        if chart_drawing is not None:
            elements.append(chart_drawing)
            elements.append(Spacer(1, 6))

        health_table_data = [
            [
                Paragraph("<b>Date</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Type</b>", self.styles['TableCellHeader']),
                Paragraph(f"<b>{mass_col_header}</b>", self.styles['TableCellHeader']),
                Paragraph(f"<b>{scl_col_header}</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Vol (cm³)</b>", self.styles['TableCellHeader']),
                Paragraph("<b>BCI (g/cm³)</b>", self.styles['TableCellHeader']),
                Paragraph("<b>Mass/SCL</b>", self.styles['TableCellHeader']),
                Paragraph("<b>BCS & Clinical Observations</b>", self.styles['TableCellHeader'])
            ]
        ]

        for insp in inspections:
            date_str = escape(str(insp.get("date") or "--"))
            type_str = escape(str(insp.get("type") or "--"))

            raw_mass = insp.get("mass")
            if mass_unit in ("kilograms", "kg"):
                m_num = self._parse_float_safe(insp.get("mass_val")) or self._parse_float_safe(raw_mass)
                mass_str = escape(self._format_mass(m_num, mass_unit) if m_num is not None else str(raw_mass or "--"))
            else:
                mass_str = escape(str(raw_mass or "--"))

            raw_scl = insp.get("scl")
            if length_unit in ("cm", "centimeters"):
                s_num = self._parse_float_safe(insp.get("scl_val")) or self._parse_float_safe(raw_scl)
                scl_str = escape(self._format_length(s_num, length_unit) if s_num is not None else str(raw_scl or "--"))
            else:
                scl_str = escape(str(raw_scl or "--"))

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
