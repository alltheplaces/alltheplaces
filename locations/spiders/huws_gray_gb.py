import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HuwsGrayGBSpider(SitemapSpider, StructuredDataSpider):
    name = "huws_gray_gb"
    item_attributes = {"brand": "Huws Gray", "brand_wikidata": "Q16965780"}
    sitemap_urls = ["https://www.huwsgray.co.uk/robots.txt"]
    sitemap_rules = [(r"/storefinder/store/.+-(\d+)$", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["city"] = None

        if m := re.search(r"storeFinder24\.InitMap\(\d+, (-?\d+\.\d+), (-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
