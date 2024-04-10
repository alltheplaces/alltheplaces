from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysSGSpider(FiveGuysCASpider):
    name = "five_guys_sg"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.sg/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.sg\/[^/]+$", "parse_sd")]
