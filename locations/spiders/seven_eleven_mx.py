from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenMXSpider(Spider):
    name = "seven_eleven_mx"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://www.7-eleven.com.mx/buscador-de-tiendas/fetch_data.php"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        store_keys = [key.removesuffix("_tienda") for key in response.json()["values"][0]]
        for store in response.json()["values"][1:]:
            store = {store_keys[i]: store[i] for i in range(len(store_keys))}
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").title()
            item["street_address"] = item.pop("addr_full")
            item["postcode"] = store.get("cp")
            if store.get("Petro Seven") == "1":
                item["located_in"] = "Petro Seven"
                item["located_in_wikidata"] = "Q118601740"
            apply_yes_no(Extras.DRIVE_THROUGH, item, store.get("7-drive") == "1")
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
