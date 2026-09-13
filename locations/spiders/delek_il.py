import re
from typing import Any

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class DelekILSpider(Spider):
    name = "delek_il"
    item_attributes = {"brand": "Delek", "brand_wikidata": "Q1184087"}
    allowed_domains = ["delek.co.il"]
    start_urls = ["https://delek.co.il/איתור-תחנה/"]

    # station flag (value "כן" = yes) -> tag
    SERVICES = {
        "gas": Fuel.LPG,  # תדלוק בגז (autogas)
        "orea": Fuel.ADBLUE,  # אוריאה
        "energy": Fuel.ELECTRIC,  # טעינה חשמלית
        "wash": Extras.CAR_WASH,  # שטיפה
        "atm": Extras.ATM,
        "disabled": Extras.WHEELCHAIR,  # מונגשת
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The station finder loads its data from a nonce-protected admin-ajax action.
        if not (nonce := re.search(r"'nonce',\s*'([0-9a-f]+)'", response.text)):
            self.logger.error("Delek stations nonce not found")
            return
        yield self.stations_request(nonce.group(1), 1)

    def stations_request(self, nonce: str, page: int) -> FormRequest:
        return FormRequest(
            url="https://delek.co.il/wp-admin/admin-ajax.php",
            formdata={"action": "sq_get_stations", "page": str(page), "nonce": nonce},
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_stations,
            cb_kwargs={"nonce": nonce},
        )

    def parse_stations(self, response: Response, nonce: str, **kwargs: Any) -> Any:
        data = response.json()["data"]
        for station in data["stations"]:
            item = DictParser.parse(station)  # id -> ref, name, lat, address -> addr_full, city
            item["ref"] = str(item["ref"])
            item["lon"] = station.get("lang")  # the source misspells "lng" as "lang"
            item["branch"] = item.pop("name", None)  # the brand name comes from NSI
            item["street_address"] = item.pop("addr_full", None)
            if station.get("hours") == "24/7":
                item["opening_hours"] = "24/7"
            apply_category(Categories.FUEL_STATION, item)

            for field, tag in self.SERVICES.items():
                apply_yes_no(tag, item, station.get(field) == "כן")

            yield item

        if next_page := data.get("next"):
            yield self.stations_request(nonce, next_page)
