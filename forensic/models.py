from django.db import models


class ImageAnalysis(models.Model):

    image = models.ImageField(
        upload_to="uploads/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    # ---------------------------------------------------------
    # Forensic scores
    # ---------------------------------------------------------

    ela_score = models.FloatField(
        default=0.0
    )

    frequency_score = models.FloatField(
        default=0.0
    )

    edge_score = models.FloatField(
        default=0.0
    )

    noise_score = models.FloatField(
        default=0.0
    )

    histogram_score = models.FloatField(
        default=0.0
    )
    copy_move_score = models.FloatField(
    default=0.0
    )

    final_score = models.FloatField(
        default=0.0
    )

    status = models.CharField(
        max_length=50,
        default="Not Analyzed"
    )

    analyzed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.image.name

