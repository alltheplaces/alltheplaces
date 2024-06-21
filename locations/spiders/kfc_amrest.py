from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.storefinders.amrest_eu import AmrestEUSpider


class KfcAmrestSpider(AmrestEUSpider):
    name = "kfc_amrest"
    item_attributes = KFC_SHARED_ATTRIBUTES
    base_urls = [
        "https://api.amrest.eu/amdv/ordering-api/KFC_PL/",  # https://kfc.pl/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_HU/",  # https://kfc.hu/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_CZ/",  # https://kfc.cz/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_HR/",  # https://kfc.hr/en/restaurants
        "https://api.amrest.eu/amdv/ordering-api/KFC_RS/",  # https://kfc.rs/en/restaurants
    ]
    base_headers = AmrestEUSpider.base_headers | {"brand": "KFC"}
    auth_data = AmrestEUSpider.auth_data | {"source": "WEB_KFC"}

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name").removeprefix("KFC ")
        yield item
