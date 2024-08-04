from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TerriblesUSSpider(AgileStoreLocatorSpider):
    name = "terribles_us"
    item_attributes = {"name": "Terrible's", "brand": "Terrible's", "brand_wikidata": "Q7703648"}
    allowed_domains = ["www.terribles.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["ref"] = item.pop("name").removeprefix("Terrible's Car Wash ")
        apply_category(Categories.CAR_WASH, item)

        yield item
