import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ReissGBSpider(SitemapSpider, StructuredDataSpider):
    name = "reiss_gb"
    item_attributes = {"brand": "Reiss", "brand_wikidata": "Q7310479"}
    sitemap_urls = ["https://www.reiss.com/robots.txt"]
    sitemap_rules = [(r"/storelocator/.+/\d+$", "parse_sd")]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"\"&daddr=\"\s*\+\s*(-?\d+\.\d+)\s*\+\s*\",\"\s*\+\s*(-?\d+\.\d+);", response.text):
            item["lat"], item["lon"] = m.groups()
        yield item
