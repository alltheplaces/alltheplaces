from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysLUSpider(FiveGuysCASpider):
    name = "five_guys_lu"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.lu/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.lu\/en_lu\/[^/]+$", "parse_sd")]
