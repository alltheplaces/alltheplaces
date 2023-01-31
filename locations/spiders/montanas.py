from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MontanasSpider(SitemapSpider, StructuredDataSpider):
    name = "montanas"
    item_attributes = {"brand": "Montana's", "brand_wikidata": "Q17022490"}
    allowed_domains = ["montanas.ca"]
    sitemap_urls = ["https://www.montanas.ca/en/locations/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]
    wanted_types = ["Restaurant"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.montanas.ca",
            "User-Agent": BROWSER_DEFAULT,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        },
    }
