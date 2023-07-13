from django.db import models
from django.utils.html import format_html

__all__ = ['UserColorProfile']

class UserColorProfile (models.Model):
    class Meta:
        verbose_name = "User Color Profile"

    background_rgb = models.CharField (max_length = 8, verbose_name = "Background RGB")
    closest_css3_color = models.CharField (max_length = 64, verbose_name = "Closest CSS3 Color (BG)")

    COLOR_SAMPLE_HTML_BLOCK = ("<span style='padding: 0.5em 10em; background-color: #{background_rgb};'>&nbsp;</span>")

    def color_sample (this):
        html_block = this.COLOR_SAMPLE_HTML_BLOCK.format (background_rgb=this.background_rgb)

        return format_html (html_block)

    def __str__ (this):
        return this.closest_css3_color
