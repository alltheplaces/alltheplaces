import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LoftUSSpider(SitemapSpider, StructuredDataSpider):
    name = "loft_us"
    item_attributes = {"brand": "Loft", "brand_wikidata": "Q62075137"}
    allowed_domains = ["stores.loft.com"]
    sitemap_urls = ["https://stores.loft.com/sitemap.xml"]
    sitemap_rules = [
        (r"/outlet/[-\w]{2}/[-\w]{2}/[-\w]+/[-\w]+.html$", "parse_sd"),
        (r"/[-\w]{2}/[-\w]+/[-\w]+.html$", "parse_sd"),
    ]
    wanted_types = ["ClothingStore"]

    def pre_process_data(self, ld_data, **kwargs):
        if ld_data["location"] == []:
            del ld_data["location"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name")
        item["branch"] = response.xpath('//div[@itemprop="name"]/div[1]/text()').get()

        if m := re.search(r"\"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)}", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
