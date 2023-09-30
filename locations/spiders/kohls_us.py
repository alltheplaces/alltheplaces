import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KohlsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kohls_us"
    item_attributes = {"brand": "Kohl's", "brand_wikidata": "Q967265"}
    allowed_domains = ["www.kohls.com"]
    sitemap_urls = ["https://www.kohls.com/sitemap_store.xml"]
    sitemap_rules = [(r"\/stores\/\w{2}\/\w+-(\d+)\.shtml$", "parse_sd")]
    wanted_types = ["DepartmentStore"]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = re.search(self.sitemap_rules[0][0], response.url).group(1)
        if "|" in item["name"]:
            item["name"] = item["name"].split("|")[0]
        item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(ld_data["openingHours"])
        yield item
