import os
import cv2


def save_image(image, output_path):
    """
    Save an OpenCV image to disk.
    """

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    success = cv2.imwrite(
        output_path,
        image
    )

    if not success:
        raise ValueError(
            f"Failed to save image: {output_path}"
        )

    return output_path