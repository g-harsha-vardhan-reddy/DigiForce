import cv2
import numpy as np

from collections import defaultdict, Counter

from PIL import Image, ImageChops, ImageEnhance

from io import BytesIO


# =============================================================
# CORE DIGITAL IMAGE PROCESSING
# =============================================================

def process_image(image_path):
    """
    Perform core Digital Image Processing operations
    on the uploaded image.
    """

    # ---------------------------------------------------------
    # 1. Read image
    # ---------------------------------------------------------

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            "Unable to read the image."
        )

    # ---------------------------------------------------------
    # 2. Resize very large images
    # ---------------------------------------------------------

    max_width = 1200
    max_height = 1200

    height, width = image.shape[:2]

    if width > max_width or height > max_height:

        scale = min(
            max_width / width,
            max_height / height
        )

        new_width = int(
            width * scale
        )

        new_height = int(
            height * scale
        )

        image = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

    # ---------------------------------------------------------
    # 3. Grayscale
    # ---------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # ---------------------------------------------------------
    # 4. Gaussian Filter
    # ---------------------------------------------------------

    gaussian = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # ---------------------------------------------------------
    # 5. Median Filter
    # ---------------------------------------------------------

    median = cv2.medianBlur(
        gray,
        5
    )

    # ---------------------------------------------------------
    # 6. Histogram
    # ---------------------------------------------------------

    histogram = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0, 256]
    )

    histogram = histogram.flatten().tolist()

    # ---------------------------------------------------------
    # 7. Sobel Edge Detection
    # ---------------------------------------------------------

    sobel_x = cv2.Sobel(
        gray,
        cv2.CV_64F,
        1,
        0,
        ksize=3
    )

    sobel_y = cv2.Sobel(
        gray,
        cv2.CV_64F,
        0,
        1,
        ksize=3
    )

    sobel_magnitude = cv2.magnitude(
        np.float32(
            np.abs(sobel_x)
        ),
        np.float32(
            np.abs(sobel_y)
        )
    )

    sobel_magnitude = cv2.normalize(
        sobel_magnitude,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    sobel_magnitude = np.uint8(
        sobel_magnitude
    )

    # ---------------------------------------------------------
    # 8. Canny Edge Detection
    # ---------------------------------------------------------

    canny = cv2.Canny(
        gray,
        100,
        200
    )

    # ---------------------------------------------------------
    # 9. Morphological Processing
    # ---------------------------------------------------------

    kernel = np.ones(
        (3, 3),
        np.uint8
    )

    dilated = cv2.dilate(
        canny,
        kernel,
        iterations=1
    )

    morphed = cv2.morphologyEx(
        dilated,
        cv2.MORPH_CLOSE,
        kernel
    )

    # ---------------------------------------------------------
    # Return core DIP results
    # ---------------------------------------------------------

    return {

        "original": image,

        "gray": gray,

        "gaussian": gaussian,

        "median": median,

        "sobel": sobel_magnitude,

        "canny": canny,

        "morphological": morphed,

        "histogram": histogram,
    }


# =============================================================
# ADVANCED DIP
# =============================================================

def advanced_process_image(image_path):
    """
    Advanced frequency-domain and image-forensic operations.
    """

    # ---------------------------------------------------------
    # Read grayscale image
    # ---------------------------------------------------------

    image = cv2.imread(
        image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:
        raise ValueError(
            "Unable to read the image."
        )

    # ---------------------------------------------------------
    # 1. DFT / FFT
    # ---------------------------------------------------------

    float_image = np.float32(
        image
    )

    dft = cv2.dft(
        float_image,
        flags=cv2.DFT_COMPLEX_OUTPUT
    )

    # Move low frequencies to the center

    dft_shift = np.fft.fftshift(
        dft
    )

    # ---------------------------------------------------------
    # Magnitude spectrum
    # ---------------------------------------------------------

    magnitude = cv2.magnitude(
        dft_shift[:, :, 0],
        dft_shift[:, :, 1]
    )

    # Log transform

    magnitude = np.log1p(
        magnitude
    )

    dft_spectrum = cv2.normalize(
        magnitude,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    dft_spectrum = np.uint8(
        dft_spectrum
    )

    # ---------------------------------------------------------
    # 2. Frequency masks
    # ---------------------------------------------------------

    rows, cols = image.shape

    center_row = rows // 2
    center_col = cols // 2

    radius = max(
        10,
        min(rows, cols) // 8
    )

    y, x = np.ogrid[
        :rows,
        :cols
    ]

    distance = np.sqrt(
        (x - center_col) ** 2
        + (y - center_row) ** 2
    )

    # Low-pass mask

    low_pass_mask = (
        distance <= radius
    ).astype(
        np.float32
    )

    # High-pass mask

    high_pass_mask = (
        distance > radius
    ).astype(
        np.float32
    )

    # ---------------------------------------------------------
    # 3. Low-pass filtering
    # ---------------------------------------------------------

    low_pass_shift = (
        dft_shift
        * low_pass_mask[
            :,
            :,
            np.newaxis
        ]
    )

    low_pass = np.fft.ifftshift(
        low_pass_shift
    )

    low_pass_image = cv2.idft(
        low_pass
    )

    low_pass_magnitude = cv2.magnitude(
        low_pass_image[:, :, 0],
        low_pass_image[:, :, 1]
    )

    low_pass_magnitude = cv2.normalize(
        low_pass_magnitude,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    low_pass_magnitude = np.uint8(
        low_pass_magnitude
    )

    # ---------------------------------------------------------
    # 4. High-pass filtering
    # ---------------------------------------------------------

    high_pass_shift = (
        dft_shift
        * high_pass_mask[
            :,
            :,
            np.newaxis
        ]
    )

    high_pass = np.fft.ifftshift(
        high_pass_shift
    )

    high_pass_image = cv2.idft(
        high_pass
    )

    high_pass_magnitude = cv2.magnitude(
        high_pass_image[:, :, 0],
        high_pass_image[:, :, 1]
    )

    high_pass_magnitude = cv2.normalize(
        high_pass_magnitude,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    high_pass_magnitude = np.uint8(
        high_pass_magnitude
    )

    # ---------------------------------------------------------
    # 5. Error Level Analysis (ELA)
    # ---------------------------------------------------------

    original_pil = Image.open(
        image_path
    ).convert(
        "RGB"
    )

    # Re-compress as JPEG

    buffer = BytesIO()

    original_pil.save(
        buffer,
        format="JPEG",
        quality=90
    )

    buffer.seek(0)

    recompressed = Image.open(
        buffer
    ).convert(
        "RGB"
    )

    # Difference

    difference = ImageChops.difference(
        original_pil,
        recompressed
    )

    # Enhance small differences

    enhanced_difference = ImageEnhance.Brightness(
        difference
    ).enhance(
        10
    )

    ela = np.array(
        enhanced_difference
    )

    # RGB -> BGR

    ela = cv2.cvtColor(
        ela,
        cv2.COLOR_RGB2BGR
    )

    # Resize ELA if required

    if ela.shape[:2] != image.shape[:2]:

        ela = cv2.resize(
            ela,
            (cols, rows),
            interpolation=cv2.INTER_AREA
        )

    return {

        "dft_spectrum": dft_spectrum,

        "low_pass": low_pass_magnitude,

        "high_pass": high_pass_magnitude,

        "ela": ela,
    }


# =============================================================
# FORENSIC SCORING
# =============================================================

def clamp_score(value):
    """
    Keep a score between 0 and 100.
    """

    return float(
        np.clip(
            value,
            0,
            100
        )
    )


# =============================================================
# NOISE SCORE
# =============================================================

def calculate_noise_score(gray):
    """
    Estimate high-frequency noise using the difference
    between the image and a median-filtered version.
    """

    median = cv2.medianBlur(
        gray,
        5
    )

    difference = cv2.absdiff(
        gray,
        median
    )

    noise_value = float(
        np.mean(
            difference
        )
    )

    score = (
        noise_value / 2.55
    )

    return clamp_score(
        score
    )


# =============================================================
# EDGE SCORE
# =============================================================

def calculate_edge_score(canny):
    """
    Calculate percentage of pixels detected as edges.
    """

    total_pixels = (
        canny.shape[0]
        * canny.shape[1]
    )

    edge_pixels = np.count_nonzero(
        canny
    )

    edge_density = (
        edge_pixels
        / total_pixels
    ) * 100

    score = (
        edge_density * 2.0
    )

    return clamp_score(
        score
    )


# =============================================================
# FREQUENCY SCORE
# =============================================================

def calculate_frequency_score(gray):
    """
    Measure the proportion of high-frequency energy
    in the image.
    """

    image_float = np.float32(
        gray
    )

    fft = np.fft.fft2(
        image_float
    )

    fft_shift = np.fft.fftshift(
        fft
    )

    magnitude = np.abs(
        fft_shift
    )

    energy = magnitude ** 2

    rows, cols = gray.shape

    center_row = rows // 2
    center_col = cols // 2

    radius = max(
        10,
        min(rows, cols) // 8
    )

    y, x = np.ogrid[
        :rows,
        :cols
    ]

    distance = np.sqrt(
        (x - center_col) ** 2
        + (y - center_row) ** 2
    )

    high_frequency_mask = (
        distance > radius
    )

    total_energy = float(
        np.sum(
            energy
        )
    )

    high_frequency_energy = float(
        np.sum(
            energy[
                high_frequency_mask
            ]
        )
    )

    if total_energy == 0:
        return 0.0

    high_frequency_ratio = (
        high_frequency_energy
        / total_energy
    )

    score = (
        high_frequency_ratio * 100
    )

    return clamp_score(
        score
    )


# =============================================================
# ELA SCORE
# =============================================================

def calculate_ela_score(ela):
    """
    Calculate the average intensity of the ELA image.
    """

    ela_gray = cv2.cvtColor(
        ela,
        cv2.COLOR_BGR2GRAY
    )

    ela_mean = float(
        np.mean(
            ela_gray
        )
    )

    score = (
        ela_mean / 2.55
    )

    return clamp_score(
        score
    )


# =============================================================
# HISTOGRAM SCORE
# =============================================================

def calculate_histogram_score(gray):
    """
    Calculate histogram entropy.

    This is treated as a supporting image characteristic,
    not as direct proof of image tampering.
    """

    histogram = cv2.calcHist(
        [gray],
        [0],
        None,
        [256],
        [0, 256]
    )

    histogram = histogram.flatten()

    total = np.sum(
        histogram
    )

    if total == 0:
        return 0.0

    probabilities = (
        histogram / total
    )

    probabilities = probabilities[
        probabilities > 0
    ]

    entropy = -np.sum(
        probabilities
        * np.log2(
            probabilities
        )
    )

    # Maximum entropy for 256 bins = 8

    score = (
        entropy / 8.0
    ) * 100

    return clamp_score(
        score
    )


# =============================================================
# COPY-MOVE DETECTION
# =============================================================

def calculate_copy_move_score(
    gray,
    block_size=32
):
    """
    Detect repeated image blocks at different locations.

    This is a heuristic copy-move indicator.

    The method:
        1. Divides the image into blocks.
        2. Creates a normalized descriptor for each block.
        3. Finds identical/very similar descriptors.
        4. Checks whether repeated blocks occur far apart.
        5. Looks for repeated displacement vectors.

    Returns a heuristic score from 0 to 100.
    """

    image = gray.copy()

    height, width = image.shape

    # ---------------------------------------------------------
    # Crop to complete blocks
    # ---------------------------------------------------------

    height = (
        height // block_size
    ) * block_size

    width = (
        width // block_size
    ) * block_size

    image = image[
        :height,
        :width
    ]

    # ---------------------------------------------------------
    # Store block signatures
    # ---------------------------------------------------------

    signatures = defaultdict(list)

    for y in range(
        0,
        height,
        block_size
    ):

        for x in range(
            0,
            width,
            block_size
        ):

            block = image[
                y:y + block_size,
                x:x + block_size
            ].astype(
                np.float32
            )

            # Ignore almost-uniform regions

            if float(
                block.std()
            ) < 8:

                continue

            # -------------------------------------------------
            # Resize block into small descriptor
            # -------------------------------------------------

            descriptor = cv2.resize(
                block,
                (8, 8),
                interpolation=cv2.INTER_AREA
            )

            # -------------------------------------------------
            # Normalize brightness and contrast
            # -------------------------------------------------

            descriptor = (
                descriptor
                - descriptor.mean()
            ) / (
                descriptor.std()
                + 1e-6
            )

            # -------------------------------------------------
            # Quantize descriptor
            # -------------------------------------------------

            descriptor = np.round(
                descriptor,
                1
            )

            signature = (
                descriptor.tobytes()
            )

            signatures[
                signature
            ].append(
                (x, y)
            )

    # ---------------------------------------------------------
    # Find repeated displacement vectors
    # ---------------------------------------------------------

    displacement_counter = Counter()

    for positions in signatures.values():

        if len(positions) < 2:
            continue

        # Avoid repetitive areas creating huge groups

        if len(positions) > 20:
            continue

        for i in range(
            len(positions)
        ):

            for j in range(
                i + 1,
                len(positions)
            ):

                x1, y1 = positions[i]

                x2, y2 = positions[j]

                distance = (
                    abs(x2 - x1)
                    + abs(y2 - y1)
                )

                # Ignore neighboring blocks

                if distance <= (
                    block_size * 2
                ):

                    continue

                dx = x2 - x1
                dy = y2 - y1

                displacement_counter[
                    (dx, dy)
                ] += 1

    # ---------------------------------------------------------
    # No repeated region
    # ---------------------------------------------------------

    if not displacement_counter:
        return 0.0

    # ---------------------------------------------------------
    # Strongest repeated displacement
    # ---------------------------------------------------------

    _, strongest_count = (
        displacement_counter.most_common(
            1
        )[0]
    )

    # Require several matching blocks

    if strongest_count < 4:
        return 0.0

    # Convert repeated matches to score

    score = (
        strongest_count * 5
    )

    return float(
        np.clip(
            score,
            0,
            100
        )
    )


# =============================================================
# COMPLETE FORENSIC ANALYSIS
# =============================================================

def calculate_forensic_scores(
    gray,
    canny,
    ela,
    copy_move_gray=None
):
    """
    Calculate all forensic indicators.

    Parameters
    ----------
    gray:
        Grayscale image used by the normal DIP pipeline.

    canny:
        Canny edge image.

    ela:
        Error Level Analysis image.

    copy_move_gray:
        Original-resolution grayscale image used specifically
        by Copy-Move Detection.

        This is important because copy-move analysis should not
        depend on a resized version of the image.
    """

    # ---------------------------------------------------------
    # 1. ELA
    # ---------------------------------------------------------

    ela_score = calculate_ela_score(
        ela
    )

    # ---------------------------------------------------------
    # 2. Frequency
    # ---------------------------------------------------------

    frequency_score = (
        calculate_frequency_score(
            gray
        )
    )

    # ---------------------------------------------------------
    # 3. Edge
    # ---------------------------------------------------------

    edge_score = (
        calculate_edge_score(
            canny
        )
    )

    # ---------------------------------------------------------
    # 4. Noise
    # ---------------------------------------------------------

    noise_score = (
        calculate_noise_score(
            gray
        )
    )

    # ---------------------------------------------------------
    # 5. Histogram
    # ---------------------------------------------------------

    histogram_score = (
        calculate_histogram_score(
            gray
        )
    )

    # ---------------------------------------------------------
    # 6. Copy-Move
    #
    # Use original-resolution image whenever available.
    # ---------------------------------------------------------

    if copy_move_gray is None:

        copy_move_gray = gray

    copy_move_score = (
        calculate_copy_move_score(
            copy_move_gray
        )
    )

    # ---------------------------------------------------------
    # 7. Baseline heuristic
    #
    # Histogram is retained as a supporting feature in the
    # existing baseline formula.
    # ---------------------------------------------------------

    baseline_score = (

        (ela_score * 0.35)

        + (
            frequency_score
            * 0.25
        )

        + (
            edge_score
            * 0.15
        )

        + (
            noise_score
            * 0.15
        )

        + (
            histogram_score
            * 0.10
        )
    )

    baseline_score = clamp_score(
        baseline_score
    )

    # ---------------------------------------------------------
    # 8. Final score
    #
    # A strong copy-move signal is not diluted by global
    # image statistics.
    # ---------------------------------------------------------

    final_score = max(
        baseline_score,
        copy_move_score
    )

    final_score = clamp_score(
        final_score
    )

    # ---------------------------------------------------------
    # 9. Classification
    # ---------------------------------------------------------

    if copy_move_score >= 60:

        status = (
            "POSSIBLE TAMPERING"
        )

    elif final_score >= 65:

        status = (
            "POSSIBLE TAMPERING"
        )

    elif final_score >= 35:

        status = (
            "UNCERTAIN"
        )

    else:

        status = (
            "LIKELY ORIGINAL"
        )

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return {

        "ela_score": round(
            ela_score,
            2
        ),

        "frequency_score": round(
            frequency_score,
            2
        ),

        "edge_score": round(
            edge_score,
            2
        ),

        "noise_score": round(
            noise_score,
            2
        ),

        "histogram_score": round(
            histogram_score,
            2
        ),

        "copy_move_score": round(
            copy_move_score,
            2
        ),

        "baseline_score": round(
            baseline_score,
            2
        ),

        "final_score": round(
            final_score,
            2
        ),

        "status": status,
    }