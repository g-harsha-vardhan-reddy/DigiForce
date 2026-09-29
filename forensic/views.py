import os

import cv2

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.contrib import messages
from django.utils import timezone

from PIL import Image

from .models import ImageAnalysis

from .dip.processing import (
    process_image,
    advanced_process_image,
    calculate_forensic_scores,
)

from .utils.image_utils import save_image

from .utils.report_generator import (
    generate_forensic_report,
)


# ============================================================
# HOME
# ============================================================

def home(request):

    images = ImageAnalysis.objects.order_by(
        "-uploaded_at"
    )

    return render(
        request,
        "index.html",
        {
            "images": images
        }
    )


# ============================================================
# IMAGE UPLOAD
# ============================================================

def upload_image(request):

    if request.method == "POST":

        uploaded_image = request.FILES.get(
            "image"
        )

        # ----------------------------------------------------
        # Check file selected
        # ----------------------------------------------------

        if not uploaded_image:

            messages.error(
                request,
                "Please select an image."
            )

            return redirect("home")

        # ----------------------------------------------------
        # Maximum file size = 10 MB
        # ----------------------------------------------------

        max_size = 10 * 1024 * 1024

        if uploaded_image.size > max_size:

            messages.error(
                request,
                "Image size must be less than 10 MB."
            )

            return redirect("home")

        # ----------------------------------------------------
        # Validate actual image content
        # ----------------------------------------------------

        try:

            image = Image.open(
                uploaded_image
            )

            image.verify()

        except Exception:

            messages.error(
                request,
                "Invalid or corrupted image file."
            )

            return redirect("home")

        # ----------------------------------------------------
        # Reset file pointer after verify()
        # ----------------------------------------------------

        uploaded_image.seek(0)

        # ----------------------------------------------------
        # Allowed image MIME types
        # ----------------------------------------------------

        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/jpg",
            "image/webp",
        ]

        if uploaded_image.content_type not in allowed_types:

            messages.error(
                request,
                "Only JPG, JPEG, PNG and WEBP images are allowed."
            )

            return redirect("home")

        # ----------------------------------------------------
        # Save image
        # ----------------------------------------------------

        ImageAnalysis.objects.create(
            image=uploaded_image
        )

        messages.success(
            request,
            "Image uploaded successfully."
        )

        return redirect("home")

    return redirect("home")


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(request, image_id):

    # --------------------------------------------------------
    # Get database record
    # --------------------------------------------------------

    image_record = get_object_or_404(
        ImageAnalysis,
        id=image_id
    )

    # --------------------------------------------------------
    # Full path of uploaded image
    # --------------------------------------------------------

    image_path = os.path.join(
        settings.MEDIA_ROOT,
        str(image_record.image)
    )

    # --------------------------------------------------------
    # ORIGINAL-RESOLUTION GRAYSCALE
    #
    # This is specifically used for Copy-Move Detection.
    # We don't use the resized DIP image for this.
    # --------------------------------------------------------

    original_gray = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if original_gray is None:

        raise ValueError(
            "Unable to read original image."
        )

    # --------------------------------------------------------
    # STEP 3 - CORE DIP
    # --------------------------------------------------------

    results = process_image(
        image_path
    )

    # --------------------------------------------------------
    # STEP 4 - ADVANCED DIP
    # --------------------------------------------------------

    advanced_results = advanced_process_image(
        image_path
    )

    # --------------------------------------------------------
    # STEP 5 - FORENSIC SCORES
    #
    # Important:
    # copy_move_gray = original-resolution image
    # --------------------------------------------------------

    forensic_scores = calculate_forensic_scores(
        gray=results["gray"],

        canny=results["canny"],

        ela=advanced_results["ela"],

        copy_move_gray=original_gray,
    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    output_dir = os.path.join(
        settings.MEDIA_ROOT,
        "results",
        str(image_id)
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # ========================================================
    # CORE DIP OUTPUTS
    # ========================================================

    image_names = {

        "gray": "grayscale.jpg",

        "gaussian": "gaussian.jpg",

        "median": "median.jpg",

        "sobel": "sobel.jpg",

        "canny": "canny.jpg",

        "morphological": "morphological.jpg",
    }

    output_files = {}

    for key, filename in image_names.items():

        output_path = os.path.join(
            output_dir,
            filename
        )

        save_image(
            results[key],
            output_path
        )

        output_files[key] = (
            settings.MEDIA_URL
            + f"results/{image_id}/{filename}"
        )

    # ========================================================
    # ADVANCED DIP OUTPUTS
    # ========================================================

    advanced_names = {

        "dft_spectrum":
            "dft_spectrum.jpg",

        "low_pass":
            "low_pass.jpg",

        "high_pass":
            "high_pass.jpg",

        "ela":
            "ela.jpg",
    }

    advanced_files = {}

    for key, filename in advanced_names.items():

        output_path = os.path.join(
            output_dir,
            filename
        )

        save_image(
            advanced_results[key],
            output_path
        )

        advanced_files[key] = (
            settings.MEDIA_URL
            + f"results/{image_id}/{filename}"
        )

    # ========================================================
    # SAVE FORENSIC SCORES
    # ========================================================

    image_record.ela_score = (
        forensic_scores["ela_score"]
    )

    image_record.frequency_score = (
        forensic_scores["frequency_score"]
    )

    image_record.edge_score = (
        forensic_scores["edge_score"]
    )

    image_record.noise_score = (
        forensic_scores["noise_score"]
    )

    image_record.histogram_score = (
        forensic_scores["histogram_score"]
    )

    # --------------------------------------------------------
    # NEW COPY-MOVE SCORE
    # --------------------------------------------------------

    image_record.copy_move_score = (
        forensic_scores["copy_move_score"]
    )

    # --------------------------------------------------------
    # BASELINE SCORE
    # --------------------------------------------------------

    image_record.final_score = (
        forensic_scores["final_score"]
    )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    image_record.status = (
        forensic_scores["status"]
    )

    # --------------------------------------------------------
    # Analysis timestamp
    # --------------------------------------------------------

    image_record.analyzed_at = (
        timezone.now()
    )

    # --------------------------------------------------------
    # Save database record
    # --------------------------------------------------------

    image_record.save()

    # ========================================================
    # RENDER DASHBOARD
    # ========================================================

    return render(
        request,
        "analysis.html",
        {
            "image": image_record,

            "results": output_files,

            "advanced_results": advanced_files,

            "histogram": results["histogram"],

            "scores": forensic_scores,
        }
    )


# ============================================================
# DOWNLOAD PDF REPORT
# ============================================================

def download_report(request, image_id):

    image_record = get_object_or_404(
        ImageAnalysis,
        id=image_id
    )

    # --------------------------------------------------------
    # If not analyzed, analyze first
    # --------------------------------------------------------

    if image_record.status == "Not Analyzed":

        return redirect(
            "analyze_image",
            image_id=image_id
        )

    # --------------------------------------------------------
    # Generate PDF
    # --------------------------------------------------------

    pdf_buffer = generate_forensic_report(
        image_record
    )

    # --------------------------------------------------------
    # PDF filename
    # --------------------------------------------------------

    filename = (
        f"digiforensics_report_"
        f"{image_id}.pdf"
    )

    # --------------------------------------------------------
    # Return PDF
    # --------------------------------------------------------

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
    )