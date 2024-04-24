from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysITSpider(FiveGuysCASpider):
    name = "five_guys_it"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.it/robots.txt"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.it\/en_it\/[^/]+$", "parse_sd")]
