import html
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CarlsJrUSSpider(SitemapSpider, StructuredDataSpider):
    name = "carls_jr_us"
    item_attributes = {"brand": "Carl's Jr.", "brand_wikidata": "Q1043486"}
    sitemap_urls = ["https://locations.carlsjr.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+/$", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = html.unescape(item["street_address"])
        item["city"] = html.unescape(item["city"])
        if ref := re.search(r" (\d+)$", item.pop("name")):
            item["ref"] = ref.group(1)
        yield item
