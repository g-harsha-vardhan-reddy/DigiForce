from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from django.conf import settings


def generate_forensic_report(image_record):
    """
    Generate a downloadable PDF forensic report
    for a single analyzed image.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=15,
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
    )

    story = []

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "DigiForensics",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Digital Image Forensics Report",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # BASIC INFORMATION
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Image Information",
            heading_style
        )
    )

    image_name = str(
        image_record.image.name
    )

    info_data = [
        ["Image", image_name],
        [
            "Uploaded",
            str(image_record.uploaded_at)
        ],
        [
            "Status",
            image_record.status
        ],
        [
            "Overall Score",
            f"{image_record.final_score:.2f}/100"
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[1.6 * inch, 4.8 * inch]
    )

    info_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(info_table)

    # ---------------------------------------------------------
    # SCORE BREAKDOWN
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Forensic Score Breakdown",
            heading_style
        )
    )

    score_data = [
        ["Indicator", "Score", "Weight"],

        [
            "ELA",
            f"{image_record.ela_score:.2f}",
            "35%"
        ],

        [
            "Frequency Analysis",
            f"{image_record.frequency_score:.2f}",
            "25%"
        ],

        [
            "Edge Analysis",
            f"{image_record.edge_score:.2f}",
            "15%"
        ],

        [
            "Noise Analysis",
            f"{image_record.noise_score:.2f}",
            "15%"
        ],

        [
            "Histogram Analysis",
            f"{image_record.histogram_score:.2f}",
            "10%"
        ],
        [
            "Copy-Move Detection",
            f"{image_record.copy_move_score:.2f}",
            "Independent",
        ],

        [
            "Final Score",
            f"{image_record.final_score:.2f}",
            "100%"
        ],
    ]

    score_table = Table(
        score_data,
        colWidths=[
            3.3 * inch,
            1.5 * inch,
            1.2 * inch,
        ]
    )

    score_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
            ]
        )
    )

    story.append(score_table)

    # ---------------------------------------------------------
    # ORIGINAL IMAGE
    # ---------------------------------------------------------

    original_path = (
        settings.MEDIA_ROOT
        / str(image_record.image)
    )

    if original_path.exists():

        story.append(
            Paragraph(
                "Original Image",
                heading_style
            )
        )

        story.append(
            Image(
                str(original_path),
                width=5.5 * inch,
                height=3.8 * inch,
            )
        )

    # ---------------------------------------------------------
    # RESULTS DIRECTORY
    # ---------------------------------------------------------

    results_dir = (
        settings.MEDIA_ROOT
        / "results"
        / str(image_record.id)
    )

    # ---------------------------------------------------------
    # ELA IMAGE
    # ---------------------------------------------------------

    ela_path = results_dir / "ela.jpg"

    if ela_path.exists():

        story.append(
            Paragraph(
                "Error Level Analysis",
                heading_style
            )
        )

        story.append(
            Image(
                str(ela_path),
                width=5.5 * inch,
                height=3.8 * inch,
            )
        )

    # ---------------------------------------------------------
    # DFT SPECTRUM
    # ---------------------------------------------------------

    dft_path = (
        results_dir
        / "dft_spectrum.jpg"
    )

    if dft_path.exists():

        story.append(
            Paragraph(
                "DFT Frequency Spectrum",
                heading_style
            )
        )

        story.append(
            Image(
                str(dft_path),
                width=5.5 * inch,
                height=3.8 * inch,
            )
        )

    # ---------------------------------------------------------
    # INTERPRETATION
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Interpretation",
            heading_style
        )
    )

    story.append(
        Paragraph(
            "Copy-Move Detection is an independent indicator "
            "that searches for repeated image regions occurring "
            "at different locations. A strong result increases "
            "the final heuristic assessment but is not definitive "
            "proof of manipulation.",
            normal_style
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer