import re
from datetime import datetime
from io import BytesIO
from typing import List
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _clean_filename(value: str) -> str:
    """Create a filesystem-safe filename stem."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return cleaned or "docmind-chat"


def _confidence_color(confidence: float):
    """Return the badge color based on the confidence score."""
    if confidence >= 80:
        return colors.HexColor("#16A34A")
    if confidence >= 50:
        return colors.HexColor("#D97706")
    return colors.HexColor("#DC2626")


def _format_message_text(content: str) -> str:
    """Escape plain text and preserve line breaks for reportlab paragraphs."""
    return escape((content or "").strip()).replace("\n", "<br/>")


def build_chat_pdf(doc_title: str, messages: List[dict]) -> tuple[BytesIO, str]:
    """Render the exported chat transcript as a styled PDF."""
    title = doc_title.strip() or "Document Chat"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=21,
        leading=25,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceAfter=4,
    )
    role_style = ParagraphStyle(
        "Role",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    message_style = ParagraphStyle(
        "Message",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
    )
    citation_style = ParagraphStyle(
        "Citation",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    story = [
        Paragraph("DocMind Chat Export", title_style),
        Paragraph(f"<b>Document:</b> {escape(title)}", meta_style),
        Paragraph(f"<b>Exported:</b> {escape(timestamp)}", meta_style),
        Spacer(1, 10),
    ]

    content_width = doc.width

    for message in messages:
        is_user = message.get("role") == "user"
        role_label = "User" if is_user else "Assistant"
        bubble_bg = colors.HexColor("#DBEAFE") if is_user else colors.white
        role_bg = colors.HexColor("#2563EB") if is_user else colors.HexColor("#0F172A")
        bubble_border = colors.HexColor("#93C5FD") if is_user else colors.HexColor("#CBD5E1")

        body_flowables = [
            Table(
                [[Paragraph(role_label, role_style)]],
                colWidths=[content_width - 40],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), role_bg),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROUNDEDCORNERS", [5, 5, 5, 5]),
                ]),
            ),
            Spacer(1, 7),
            Paragraph(_format_message_text(message.get("content", "")) or "&nbsp;", message_style),
        ]

        confidence = message.get("confidence")
        if confidence is not None:
            badge_color = _confidence_color(float(confidence))
            body_flowables.extend([
                Spacer(1, 8),
                Table(
                    [[Paragraph(f"Confidence {float(confidence):.1f}%", badge_style)]],
                    style=TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), badge_color),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
                    ]),
                ),
            ])

        citations = message.get("citations") or []
        if citations:
            body_flowables.extend([
                Spacer(1, 10),
                Paragraph("<b>Citations</b>", citation_style),
                Spacer(1, 4),
            ])
            for idx, citation in enumerate(citations, start=1):
                doc_name = escape(citation.get("doc_name", "Unknown"))
                chunk_index = citation.get("chunk_index", 0)
                excerpt = _format_message_text(citation.get("excerpt", ""))
                citation_html = (
                    f"{idx}. <b>{doc_name}</b> - chunk {chunk_index}<br/>"
                    f"{excerpt or 'No excerpt available.'}"
                )
                body_flowables.extend([
                    Paragraph(citation_html, citation_style),
                    Spacer(1, 3),
                ])

        bubble = Table(
            [[body_flowables]],
            colWidths=[content_width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bubble_bg),
                ("BOX", (0, 0), (-1, -1), 1, bubble_border),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("ROUNDEDCORNERS", [12, 12, 12, 12]),
            ]),
        )

        story.extend([bubble, Spacer(1, 10)])

    doc.build(story)
    buffer.seek(0)
    filename = f"{_clean_filename(title)}-chat-export.pdf"
    return buffer, filename
