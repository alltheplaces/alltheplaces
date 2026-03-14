from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HobbycraftGBSpider(CrawlSpider, StructuredDataSpider):
    name = "hobbycraft_gb"
    item_attributes = {"brand": "Hobbycraft", "brand_wikidata": "Q16984508"}
    start_urls = ["https://www.hobbycraft.co.uk/storelist/"]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item.pop("facebook", None)
        item.pop("image", None)
        item.pop("twitter", None)

        apply_category(Categories.SHOP_CRAFT, item)

        yield item
