from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class JennyCraigSpider(SitemapSpider, StructuredDataSpider):

    name = "jenny_craig"
    item_attributes = {"brand": "Jenny Craig", "brand_wikidata": "Q6179221"}
    allowed_domains = ["locations.jennycraig.com"]
    sitemap_urls = ("https://locations.jennycraig.com/robots.txt",)
    sitemap_rules = [
        (
            r"^https://locations.jennycraig.com/[^/]+/[^/]+/weight-loss-center-[^/]+.html$",
            "parse_sd",
        ),
    ]
    wanted_types = ["HealthAndBeautyBusiness"]
