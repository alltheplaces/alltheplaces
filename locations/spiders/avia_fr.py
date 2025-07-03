from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class AviaFRSpider(Spider):
    name = "avia_fr"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    AVIA_XPRESS = {"brand": "Avia XPress", "brand_wikidata": "Q124611203"}
    user_agent = BROWSER_DEFAULT
    start_urls = ["https://www.avia-france.fr/wp-admin/admin-ajax.php?action=get_avia_csv"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            if any(store.get(key, "").upper() == "TRUE" for key in ["Station temporarily closed", "Fuel agency"]):
                continue
            store["lat"], store["lon"] = [store[key].replace(",", ".") for key in ["geo lat", "geo long"]]
            store["postcode"] = store.pop("ZIP Code")
            item = DictParser.parse(store)
            item["ref"] = store.get("UID")
            item["housenumber"] = store.get("House nb.")
            item["name"] = store.get("Company name")
            item["phone"] = "; ".join(
                filter(
                    None,
                    [
                        store.get("Phone No."),
                        store.get("Mobile"),
                    ],
                )
            )
            if store.get("XPRESS", "").upper() == "TRUE":
                item.update(self.AVIA_XPRESS)
            apply_category(Categories.FUEL_STATION, item)
            yield item
