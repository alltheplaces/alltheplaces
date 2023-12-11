import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AutoZoneUSSpider(SitemapSpider, StructuredDataSpider):
    name = "auto_zone_us"
    item_attributes = {"brand": "AutoZone", "brand_wikidata": "Q4826087"}
    allowed_domains = ["www.autozone.com"]
    sitemap_urls = ["https://www.autozone.com/locations/sitemap.xml"]
    sitemap_rules = [(r"https://www.autozone.com/locations/([-\w]+)\/([-\w]+)\/([-\w]+).html$", "parse")]
    wanted_types = ["AutoPartsStore"]
    user_agent = BROWSER_DEFAULT

    def inspect_item(self, item, response):
        name = response.xpath('//h1[@id="location-name"]/span[2]/text()').get()
        item["ref"] = re.findall(r"#[0-9]+", name.strip())[0] if name else response.url
        item["image"] = None
        yield item
