from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class OfficeDepotFRSpider(CrawlSpider, StructuredDataSpider):
    name = "office_depot_fr"
    item_attributes = {
        "brand": "Office Depot",
        "brand_wikidata": "Q1337797",
    }
    allowed_domains = ["officedepot.fr"]
    start_urls = ["https://officedepot.fr/nos-magasins"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/description-magasin/magasin-office-depot-"),
            callback="parse",
            follow=True,
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.SHOP_STATIONERY, item)
        if item.get("facebook") == "https://www.facebook.com/OfficeDepot.fr":
            item["facebook"] = None
        item["branch"] = item.pop("name").removeprefix("Office DEPOT ")
        yield item
