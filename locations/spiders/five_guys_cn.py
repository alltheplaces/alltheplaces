from locations.spiders.five_guys_ca import FiveGuysCASpider
from locations.spiders.five_guys_us import FiveGuysUSSpider


class FiveGuysCNSpider(FiveGuysCASpider):
    name = "five_guys_cn"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.cn/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.cn\/en\/[^/]+$", "parse_sd")]
