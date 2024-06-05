from locations.spiders.five_guys_ae import FiveGuysAESpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysAUSpider(FiveGuysAESpider):
    name = "five_guys_au"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.com\.au\/(?!(index\.html$|search$))[^/]+$", "parse_sd")]
