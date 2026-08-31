from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# API weekday field prefixes (e.g. "pondelok_od"/"pondelok_do") mapped to OSM days.
DAYS = {
    "pondelok": "Mo",
    "utorok": "Tu",
    "streda": "We",
    "stvrtok": "Th",
    "piatok": "Fr",
    "sobota": "Sa",
    "nedela": "Su",
}


class ThreehundredsixtyfiveBankSKSpider(Spider):
    name = "365_bank_sk"
    item_attributes = {"brand": "365.bank", "brand_wikidata": "Q7237158"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://365.bank/api/branch/", data={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location_type = location["type"]
            if location_type == "posta":
                continue  # Slovak Post offices, not 365.bank locations

            item = DictParser.parse(location)
            # DictParser maps name/lat/lon; the remaining fields use Slovak keys and are set explicitly.
            item["ref"] = location["ident"]
            item["street_address"] = location.get("ulica")
            item["city"] = location.get("mesto")
            item["postcode"] = location.get("psc")
            item["state"] = location.get("kraj")
            item.pop("phone", None)  # a single generic call-centre number, not location-specific
            apply_yes_no(Extras.WHEELCHAIR, item, location.get("bezbarierovy_pristup") == 1)

            if location_type == "bankomat":
                apply_category(Categories.ATM, item)
            elif location_type in ("pobocka", "bankaNaPoste"):
                item["branch"] = item.pop("name", None)
                apply_yes_no(Extras.ATM, item, location.get("bankomat") == 1)
                item["opening_hours"] = self.parse_hours(location)
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    def parse_hours(self, location: dict[str, Any]) -> OpeningHours | None:
        hours = OpeningHours()
        has_lunch_break = location.get("obedna_prestavka") == 1
        try:
            for day, osm_day in DAYS.items():
                if not (open_time := location.get(f"{day}_od")) or not (close_time := location.get(f"{day}_do")):
                    continue
                if has_lunch_break and location.get("obedna_prestavka_od") and location.get("obedna_prestavka_do"):
                    hours.add_range(osm_day, open_time, location["obedna_prestavka_od"])
                    hours.add_range(osm_day, location["obedna_prestavka_do"], close_time)
                else:
                    hours.add_range(osm_day, open_time, close_time)
        except (KeyError, ValueError) as error:
            self.logger.warning("Could not parse hours for {}: {}".format(location.get("ident"), error))
            return None
        return hours or None
