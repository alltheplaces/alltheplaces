from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysKRSpider(FiveGuysCASpider):
    name = "five_guys_kr"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.co.kr/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.co\.kr\/en\/(?!search$)[^/]+$", "parse_sd")]
