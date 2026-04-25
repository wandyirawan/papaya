from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from typing import Dict, Any


def generate_recommendation_pdf(
    recommendation: Dict[str, Any],
    weather: Dict[str, Any],
    crop_type: str,
    location: str,
    created_at: datetime
) -> bytes:
    """
    Generate a PDF report from recommendation data.
    
    Args:
        recommendation: The AI recommendation dict
        weather: Weather data dict
        crop_type: Type of crop
        location: Location string
        created_at: Timestamp of creation
        
    Returns:
        PDF bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Container for elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#ff6b35'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4ecdc4'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    # Title
    elements.append(Paragraph("🍉 Papaya AI", title_style))
    elements.append(Paragraph("Smart Farming Recommendations", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Metadata Table
    metadata_data = [
        ["Crop Type:", crop_type.capitalize()],
        ["Location:", location],
        ["Generated:", created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ["Confidence:", f"{recommendation.get('confidence', 0.0):.0%}"]
    ]
    
    metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4*inch])
    metadata_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(metadata_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph("Executive Summary", section_style))
    elements.append(Paragraph(recommendation.get("summary", "No summary available"), body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Fertilization
    elements.append(Paragraph("Fertilization Recommendations", section_style))
    fert = recommendation.get("fertilization", {})
    fert_data = [
        ["Type:", fert.get("recommended_type", "N/A")],
        ["Timing:", fert.get("timing", "N/A")],
        ["Dosage:", fert.get("dosage", "N/A")],
        ["Notes:", fert.get("notes", "N/A")]
    ]
    fert_table = Table(fert_data, colWidths=[1.2*inch, 4.3*inch])
    fert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff8f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(fert_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Irrigation
    elements.append(Paragraph("Irrigation Recommendations", section_style))
    irr = recommendation.get("irrigation", {})
    irr_text = f"""
    <b>Should Irrigate:</b> {'Yes' if irr.get('should_irrigate') else 'No'}<br/>
    <b>Timing:</b> {irr.get('timing', 'N/A')}<br/>
    <b>Amount:</b> {irr.get('amount', 'N/A')}<br/>
    <b>Reason:</b> {irr.get('reason', 'N/A')}
    """
    elements.append(Paragraph(irr_text, body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # New page for pest and general care
    elements.append(PageBreak())
    
    # Pest & Disease
    elements.append(Paragraph("Pest & Disease Risk Assessment", section_style))
    pest = recommendation.get("pest_disease", {})
    risk = pest.get("risk_level", "unknown")
    risk_colors = {"low": "green", "medium": "orange", "high": "red"}
    risk_color = risk_colors.get(risk, "black")
    
    elements.append(Paragraph(f"<b>Risk Level:</b> <font color={risk_color}>{risk.upper()}</font>", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Potential Issues:</b>", body_style))
    for issue in pest.get("potential_issues", []):
        elements.append(Paragraph(f"• {issue}", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Preventive Measures:</b>", body_style))
    for measure in pest.get("preventive_measures", []):
        elements.append(Paragraph(f"• {measure}", body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # General Care
    elements.append(Paragraph("General Care Guidelines", section_style))
    care = recommendation.get("general_care", {})
    
    elements.append(Paragraph("<b>Daily Tasks:</b>", body_style))
    for task in care.get("daily_tasks", []):
        elements.append(Paragraph(f"• {task}", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Weekly Tasks:</b>", body_style))
    for task in care.get("weekly_tasks", []):
        elements.append(Paragraph(f"• {task}", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Paragraph("<b>Warnings:</b>", body_style))
    for warning in care.get("warnings", []):
        elements.append(Paragraph(f"⚠️ {warning}", body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Weather Context
    elements.append(Paragraph("Weather Context", section_style))
    elements.append(Paragraph(recommendation.get("weather_context", "N/A"), body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("— Generated by Papaya AI —", footer_style))
    elements.append(Paragraph(f"Report ID: {created_at.strftime('%Y%m%d%H%M%S')}", footer_style))
    
    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
