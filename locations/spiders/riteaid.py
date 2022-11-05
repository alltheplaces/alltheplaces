from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class RiteAidSpider(SitemapSpider, StructuredDataSpider):
    name = "riteaid"
    item_attributes = {"brand": "Rite Aid", "brand_wikidata": "Q3433273"}
    allowed_domains = ["riteaid.com"]
    sitemap_urls = ("https://locations2.riteaid.com.yext-cdn.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://www.riteaid.com/locations/[^/]+/[^/]+/[^/]+.html$", "parse_sd"),
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    wanted_types = ["Store"]
    download_delay = 2.0
