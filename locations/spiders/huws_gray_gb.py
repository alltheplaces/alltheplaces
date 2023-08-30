import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HuwsGrayGBSpider(SitemapSpider, StructuredDataSpider):
    name = "huws_gray_gb"
    item_attributes = {"brand": "Huws Gray", "brand_wikidata": "Q16965780"}
    sitemap_urls = ["https://www.huwsgray.co.uk/robots.txt"]
    sitemap_rules = [(r"/storefinder/store/.+-(\d+)$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["city"] = None

        if m := re.search(r"storeLocator.initializeSimple\(\d+, (-?\d+\.\d+), (-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
