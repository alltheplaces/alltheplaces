import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SecurityPublicStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "security_public_storage_us"
    item_attributes = {
        "brand": "Security Public Storage",
        "brand_wikidata": "Q130379217",
        "name": "Security Public Storage",
    }
    sitemap_urls = ["https://www.securitypublicstorage.com/location-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]

    def pre_process_data(self, ld_data, **kwargs):
        if specs := ld_data.get("openingHoursSpecification"):
            ld_data["openingHoursSpecification"] = [s for s in specs if s.get("name") == "Office Hours"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("lat"):
            return
        item.pop("name", None)
        address_lines = response.css(".location-string ::text").getall()
        item["street_address"] = address_lines[0].strip()
        if m := re.match(r"(.+) ([A-Z]{2}) (\d{5})", address_lines[1].strip()):
            item["city"], item["state"], item["postcode"] = m.groups()
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
