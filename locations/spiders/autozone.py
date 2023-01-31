import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AutoZoneSpider(SitemapSpider, StructuredDataSpider):
    name = "auto_zone"
    item_attributes = {"brand": "AutoZone", "brand_wikidata": "Q4826087"}
    allowed_domains = ["www.autozone.com"]
    sitemap_urls = ["https://www.autozone.com/locations/sitemap.xml"]
    sitemap_rules = [(r"https://www.autozone.com/locations/([-\w]+)\/([-\w]+)\/([-\w]+).html$", "parse")]
    wanted_types = ["AutoPartsStore"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.autozone.com",
            "Accept": "*/*",
            "User-Agent": BROWSER_DEFAULT,
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
        }
    }

    def inspect_item(self, item, response):
        name = response.xpath('//h1[@id="location-name"]/span[2]/text()').get()
        item["ref"] = re.findall(r"#[0-9]+", name.strip())[0] if name else response.url
        item["image"] = None
        yield item
