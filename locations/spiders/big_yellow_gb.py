import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BigYellowGBSpider(SitemapSpider, StructuredDataSpider):
    name = "big_yellow_gb"
    item_attributes = {"brand": "Big Yellow", "brand_wikidata": "Q4906703"}
    sitemap_urls = ["https://www.bigyellow.co.uk/sitemap.xml"]
    sitemap_rules = [("/*-self-storage-units/", "parse")]
    wanted_types = ["SelfStorage"]
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"\"lat\":\"(-?\d+\.\d+)\",\"lng\":\"(-?\d+\.\d+)\"", response.text):
            item["lat"], item["lon"] = m.groups()
        yield item
