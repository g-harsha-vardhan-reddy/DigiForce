import os
import tempfile

import cv2
import requests
import cloudinary
import cloudinary.uploader

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


# =========================================================
# HOME
# =========================================================

def home(request):
    images = ImageAnalysis.objects.order_by("-uploaded_at")

    return render(
        request,
        "index.html",
        {
            "images": images
        }
    )


# =========================================================
# UPLOAD IMAGE
# =========================================================

def upload_image(request):

    if request.method == "POST":

        uploaded_image = request.FILES.get("image")

        if not uploaded_image:
            messages.error(
                request,
                "Please select an image."
            )

            return redirect("home")

        # -------------------------------------------------
        # Maximum file size: 10 MB
        # -------------------------------------------------

        max_size = 10 * 1024 * 1024

        if uploaded_image.size > max_size:

            messages.error(
                request,
                "Image size must be less than 10 MB."
            )

            return redirect("home")

        # -------------------------------------------------
        # Validate image
        # -------------------------------------------------

        try:

            image = Image.open(uploaded_image)

            image.verify()

        except Exception:

            messages.error(
                request,
                "Invalid or corrupted image file."
            )

            return redirect("home")

        uploaded_image.seek(0)

        # -------------------------------------------------
        # Validate file type
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Save using Django default storage
        # -------------------------------------------------

        ImageAnalysis.objects.create(
            image=uploaded_image
        )

        messages.success(
            request,
            "Image uploaded successfully."
        )

        return redirect("home")

    return redirect("home")


# =========================================================
# DOWNLOAD CLOUDINARY IMAGE TO TEMPORARY FILE
# =========================================================

def download_image_to_temp(image_url):

    response = requests.get(
        image_url,
        timeout=60
    )

    response.raise_for_status()

    # -----------------------------------------------------
    # Determine file extension
    # -----------------------------------------------------

    suffix = ".jpg"

    lower_url = image_url.lower()

    if ".png" in lower_url:

        suffix = ".png"

    elif ".webp" in lower_url:

        suffix = ".webp"

    elif ".jpeg" in lower_url:

        suffix = ".jpeg"

    # -----------------------------------------------------
    # Create temporary file
    # -----------------------------------------------------

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    try:

        temp_file.write(
            response.content
        )

        temp_file.flush()

    finally:

        temp_file.close()

    return temp_file.name


# =========================================================
# UPLOAD ANALYSIS RESULT TO CLOUDINARY
# =========================================================

def upload_result_to_cloudinary(
    file_path,
    image_id,
    filename
):

    public_id = (
        f"digiforce/results/"
        f"{image_id}/"
        f"{os.path.splitext(filename)[0]}"
    )

    result = cloudinary.uploader.upload(
        file_path,
        public_id=public_id,
        resource_type="image",
        overwrite=True
    )

    return result["secure_url"]


# =========================================================
# ANALYZE IMAGE
# =========================================================

def analyze_image(request, image_id):

    image_record = get_object_or_404(
        ImageAnalysis,
        id=image_id
    )

    temporary_original = None

    result_temp_files = []

    try:

        # -------------------------------------------------
        # Get Cloudinary image URL
        # -------------------------------------------------

        image_url = image_record.image.url

        # -------------------------------------------------
        # Download original image temporarily
        # -------------------------------------------------

        temporary_original = download_image_to_temp(
            image_url
        )

        # -------------------------------------------------
        # Read original image
        # -------------------------------------------------

        original_gray = cv2.imread(
            temporary_original,
            cv2.IMREAD_GRAYSCALE
        )

        if original_gray is None:

            raise ValueError(
                "Unable to read original image."
            )

        # -------------------------------------------------
        # Core DIP processing
        # -------------------------------------------------

        results = process_image(
            temporary_original
        )

        # -------------------------------------------------
        # Advanced forensic processing
        # -------------------------------------------------

        advanced_results = advanced_process_image(
            temporary_original
        )

        # -------------------------------------------------
        # Calculate forensic scores
        # -------------------------------------------------

        forensic_scores = calculate_forensic_scores(
            gray=results["gray"],
            canny=results["canny"],
            ela=advanced_results["ela"],
            copy_move_gray=original_gray,
        )

        # =================================================
        # CORE RESULT IMAGES
        # =================================================

        image_names = {

            "gray":
                "grayscale.jpg",

            "gaussian":
                "gaussian.jpg",

            "median":
                "median.jpg",

            "sobel":
                "sobel.jpg",

            "canny":
                "canny.jpg",

            "morphological":
                "morphological.jpg",
        }

        output_files = {}

        for key, filename in image_names.items():

            temp_output = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            )

            temp_output.close()

            result_temp_files.append(
                temp_output.name
            )

            # ---------------------------------------------
            # Save processed image locally
            # ---------------------------------------------

            save_image(
                results[key],
                temp_output.name
            )

            # ---------------------------------------------
            # Upload to Cloudinary
            # ---------------------------------------------

            output_files[key] = (
                upload_result_to_cloudinary(
                    temp_output.name,
                    image_id,
                    filename
                )
            )

        # =================================================
        # ADVANCED RESULT IMAGES
        # =================================================

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

            temp_output = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            )

            temp_output.close()

            result_temp_files.append(
                temp_output.name
            )

            # ---------------------------------------------
            # Save advanced result
            # ---------------------------------------------

            save_image(
                advanced_results[key],
                temp_output.name
            )

            # ---------------------------------------------
            # Upload to Cloudinary
            # ---------------------------------------------

            advanced_files[key] = (
                upload_result_to_cloudinary(
                    temp_output.name,
                    image_id,
                    filename
                )
            )

        # =================================================
        # SAVE FORENSIC SCORES
        # =================================================

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

        image_record.copy_move_score = (
            forensic_scores["copy_move_score"]
        )

        image_record.final_score = (
            forensic_scores["final_score"]
        )

        image_record.status = (
            forensic_scores["status"]
        )

        image_record.analyzed_at = (
            timezone.now()
        )

        image_record.save()

        # =================================================
        # RENDER ANALYSIS PAGE
        # =================================================

        return render(
            request,
            "analysis.html",
            {
                "image": image_record,

                "results": output_files,

                "advanced_results":
                    advanced_files,

                "histogram":
                    results["histogram"],

                "scores":
                    forensic_scores,
            }
        )

    finally:

        # -------------------------------------------------
        # Delete temporary original
        # -------------------------------------------------

        if (
            temporary_original
            and os.path.exists(
                temporary_original
            )
        ):

            os.remove(
                temporary_original
            )

        # -------------------------------------------------
        # Delete temporary result files
        # -------------------------------------------------

        for temp_file in result_temp_files:

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )


# =========================================================
# DOWNLOAD FORENSIC REPORT
# =========================================================

def download_report(
    request,
    image_id
):

    image_record = get_object_or_404(
        ImageAnalysis,
        id=image_id
    )

    if image_record.status == "Not Analyzed":

        return redirect(
            "analyze_image",
            image_id=image_id
        )

    pdf_buffer = generate_forensic_report(
        image_record
    )

    filename = (
        f"digiforensics_report_"
        f"{image_id}.pdf"
    )

    return FileResponse(
        pdf_buffer,
        as_attachment=True,
        filename=filename,
    )