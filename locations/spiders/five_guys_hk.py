from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysHKSpider(FiveGuysCASpider):
    name = "five_guys_hk"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.hk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/restaurants\.fiveguys\.com\.hk\/en_hk\/(?!search$)[^/]+$", "parse_sd")]
