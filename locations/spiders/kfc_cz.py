from unidecode import unidecode

from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.storefinders.amrest_eu import AmrestEUSpider


class KfcCZSpider(AmrestEUSpider):
    name = "kfc_cz"
    item_attributes = KFC_SHARED_ATTRIBUTES
    api_brand_key = "KFC"
    api_brand_country_key = "KFC_CZ"
    api_source = "WEB"
    api_auth_source = "WEB_KFC"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("KFC ")
        item["website"] = (
            "https://kfc.cz/en/restaurants/"
            + unidecode(location["name"]).lower().replace(" - ", "-").replace(" ", "-")
            + "-"
            + item["ref"]
        )
        yield item
