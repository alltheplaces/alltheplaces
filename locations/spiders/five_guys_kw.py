from locations.spiders.five_guys_ae import FiveGuysAESpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysKWSpider(FiveGuysAESpider):
    name = "five_guys_kw"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.kw/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.com\.kw\/en_kw\/[^/]+$", "parse_sd")]
