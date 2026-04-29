import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _to_list(value):
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def _build_section(title, items, body_style, heading_style):
    story = [Paragraph(title, heading_style), Spacer(1, 0.12 * inch)]
    values = _to_list(items)
    if not values:
        story.append(Paragraph("Not available.", body_style))
    else:
        for item in values:
            story.append(Paragraph(f"- {item}", body_style))
            story.append(Spacer(1, 0.08 * inch))
    story.append(Spacer(1, 0.12 * inch))
    return story


def _format_case_summary(report_data: dict):
    case_summary = report_data.get("case_summary") or {}
    collected_info = report_data.get("collected_info") or {}

    organization = case_summary.get("organization") or collected_info.get("organization") or collected_info.get("employer_name")
    duration = case_summary.get("duration") or collected_info.get("duration")
    issue = case_summary.get("issue") or collected_info.get("issue")
    issue_description = case_summary.get("issue_description") or collected_info.get("issue_text")

    rows = []
    if organization:
        rows.append(f"Employer: {organization}")
    if issue:
        rows.append(f"Issue: {str(issue).replace('_', ' ')}")
    if duration:
        rows.append(f"Duration: {duration}")
    if issue_description:
        rows.append(f"Issue Description: {issue_description}")

    return rows


def generate_document(report_data: dict):
    output_path = os.path.join(BASE_DIR, "generated_legal_report.pdf")
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.white,
        leading=22,
        alignment=0,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#394150"),
        leading=14,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#0F172A"),
        leading=16,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        textColor=colors.HexColor("#1F2937"),
        leading=15,
        spaceAfter=4,
    )

    date_text = datetime.now().strftime("%d %b %Y")
    summary = report_data.get("summary") or report_data.get("response") or "No summary available."
    case_summary_lines = _format_case_summary(report_data)
    location_info = []
    for location in _to_list(report_data.get("locations")):
        if isinstance(location, dict):
            location_info.append(
                f"{location.get('name', 'Office')} - {location.get('address', '')} - "
                f"{location.get('phone', '')} - {location.get('hours', '')}"
            )
        else:
            location_info.append(str(location))

    header = Table(
        [[Paragraph("LegalEase AI", title_style)]],
        colWidths=[7.1 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    separator = Table([[""]], colWidths=[7.1 * inch], rowHeights=[1])
    separator.setStyle(
        TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CBD5E1"))])
    )

    story = [
        header,
        Spacer(1, 0.18 * inch),
        Paragraph("<b>LegalEase AI Report</b>", heading_style),
        Paragraph(f"Date: {date_text}", meta_style),
        Spacer(1, 0.12 * inch),
        separator,
        Spacer(1, 0.18 * inch),
        Paragraph("User Issue Summary", heading_style),
        Paragraph(summary, body_style),
        Spacer(1, 0.12 * inch),
    ]

    story.extend(_build_section("Case Summary", case_summary_lines, body_style, heading_style))

    story.extend(_build_section("Rights", report_data.get("rights"), body_style, heading_style))
    story.extend(_build_section("Steps", report_data.get("steps"), body_style, heading_style))
    story.extend(_build_section("Documents Required", report_data.get("documents"), body_style, heading_style))
    story.extend(_build_section("Location Info", location_info, body_style, heading_style))

    doc.build(story)
    return output_path
