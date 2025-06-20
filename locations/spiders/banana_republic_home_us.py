from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BananaRepublicHomeUSSpider(CrawlSpider, StructuredDataSpider):
    name = "banana_republic_home_us"
    item_attributes = {
        "brand": "Banana Republic Home",
        "brand_wikidata": "Q129793169",
    }
    start_urls = ["https://bananarepublic.gap.com/stores#browse-by-state-section"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/stores/[^/]+/$"),
        ),
        Rule(
            LinkExtractor(allow=r"/stores/[^/]+/[^/]+/$"),
        ),
        Rule(LinkExtractor(allow=r"/stores/[^/]+/[^/]+/[^/]+$"), "parse_sd"),
    ]

    # wanted_types = ["ClothingStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removesuffix("| Banana Republic")
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
