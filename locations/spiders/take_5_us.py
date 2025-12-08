from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class Take5USSpider(SitemapSpider, StructuredDataSpider):
    name = "take_5_us"
    item_attributes = {"brand": "Take 5", "brand_wikidata": "Q112359190"}
    sitemap_urls = ["https://www.take5.com/sitemap-0.xml"]
    sitemap_rules = [(r"/locations/oil-change", "parse_sd"), (r"/locations/car-wash", "parse_sd")]
    wanted_types = ["AutoRepair", "AutoWash"]

    def post_process_item(self, item, response, ld_data):
        if ld_data["@type"] == "AutoWash":
            apply_category(Categories.CAR_WASH, item)
        else:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
