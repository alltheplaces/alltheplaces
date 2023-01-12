from locations.categories import Categories
from locations.storefinders.woosmap import WoosmapSpider


class TotalEnergiesSpider(WoosmapSpider):
    name = "totalenergies"
    item_attributes = {
        "brand": "TotalEnergies",
        "brand_wikidata": "Q154037",
        "extras": Categories.FUEL_STATION.value,
    }
    key = "mapstore-prod-woos"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Origin": "https://totalenergies.com"},
    }

    def parse_item(self, item, feature, **kwargs):
        item["website"] = f'https://store.totalenergies.fr/en_EN/{item["ref"]}'

        yield item
