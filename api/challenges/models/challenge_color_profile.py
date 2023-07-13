from django.db import models
from django.utils.html import format_html

class ChallengeColorProfile (models.Model):
    class Meta:
        verbose_name = "Challenge Color Profile"

    background_rgb = models.CharField (max_length = 8, verbose_name = "Background RGB")
    title_rgb = models.CharField (max_length = 8, verbose_name = "Title RGB")
    description_rgb = models.CharField (max_length = 8, verbose_name = "Description RGB")
    closest_css3_color = models.CharField (max_length = 64, verbose_name = "Closest CSS3 Color (BG)")

    COLOR_SAMPLE_DIV_STYLE = (
        "width: 15em; " +
        "padding: 0.5em 1em; " +
        "background-color: #{background_rgb}; " +
        "line-height: 1.2;")
    COLOR_SAMPLE_TITLE_STYLE = (
        "font-size: 2em; " +
        "font-weight: 900; " +
        "color: #{title_rgb};")
    COLOR_SAMPLE_DESCRIPTION_STYLE = (
        "font-size: 1.25em; " +
        "color: #{description_rgb};")
    COLOR_SAMPLE_HTML_BLOCK = (
        "<div style='{div_style}'>" +
        "<span style='{title_style}'>CHALLENGE</span><br/>" +
        "<span style='{description_style}'>Description</span>" +
        "</div>")

    def color_sample (this):
        div_style = this.COLOR_SAMPLE_DIV_STYLE.format (background_rgb=this.background_rgb)
        title_style = this.COLOR_SAMPLE_TITLE_STYLE.format (title_rgb=this.title_rgb)
        description_style = this.COLOR_SAMPLE_DESCRIPTION_STYLE.format (description_rgb=this.description_rgb)
        html_block = this.COLOR_SAMPLE_HTML_BLOCK.format (div_style=div_style, title_style=title_style, description_style=description_style)

        return format_html (html_block)

    def __str__ (this):
        return this.closest_css3_color
