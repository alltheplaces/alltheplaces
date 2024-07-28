from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysSASpider(FiveGuysCASpider):
    name = "five_guys_sa"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.sa/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.sa\/en_sa\/[^/]+$", "parse_sd")]
