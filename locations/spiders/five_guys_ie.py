from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysIESpider(FiveGuysCASpider):
    name = "five_guys_ie"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ie/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ie\/[^/]+$", "parse_sd")]
