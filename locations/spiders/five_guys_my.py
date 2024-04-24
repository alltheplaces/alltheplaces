from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysMYSpider(FiveGuysCASpider):
    name = "five_guys_my"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.my/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.my\/en\/[^/]+$", "parse_sd")]
