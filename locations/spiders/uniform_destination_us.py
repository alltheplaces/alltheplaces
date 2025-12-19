from locations.categories import Categories, apply_category
from locations.storefinders.storepoint import StorepointSpider


class UniformDestinationUSSpider(StorepointSpider):
    name = "uniform_destination_us"
    item_attributes = {
        "brand": "Uniform Destination",
        "brand_wikidata": "Q110677262",
    }
    key = "16320dcfe5d843"

    def parse_item(self, item, location):
        apply_category(Categories.SHOP_CLOTHES, item)

        item["branch"] = location.get("description")
        item["addr_full"] = location.get("streetaddress")

        yield item
