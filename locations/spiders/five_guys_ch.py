from locations.spiders.five_guys_ae import FiveGuysAESpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysCHSpider(FiveGuysAESpider):
    name = "five_guys_ch"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ch/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ch\/en_ch\/[^/]+$", "parse_sd")]
