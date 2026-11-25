from typing import Any, AsyncIterator

import chompjs
from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_UA, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class UkrsibbankUASpider(Spider):
    name = "ukrsibbank_ua"
    item_attributes = {"brand": "UkrSibbank", "brand_wikidata": "Q1976290"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[FormRequest]:
        for term in ["viddilennya", "bankomaty"]:
            yield FormRequest(
                "https://ukrsibbank.com/wp-admin/admin-ajax.php",
                formdata={"action": "update_maps", "maps_term": term, "options[]": "all", "city_id": "0"},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = chompjs.parse_js_object(response.text, json_params={"strict": False})
        for term, features in locations.items():
            for ref, location in features.items():
                item = Feature()
                item["ref"] = ref
                item["lat"] = location["lat"]
                item["lon"] = location["lng"]
                item["addr_full"] = location["address_full"]
                item["street_address"] = location["address"]
                item["city"] = location["address_full"].split(",")[0]

                item["opening_hours"] = OpeningHours()
                if location["week"] == "Цілодобово":
                    item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
                else:
                    item["opening_hours"].add_ranges_from_string(
                        "; ".join([location["week"], location["week_sat"], location["week_sun"]]), days=DAYS_UA
                    )

                if term == "viddilennya":
                    item["branch"] = location["format_title"]
                    apply_category(Categories.BANK, item)
                else:
                    apply_category(Categories.ATM, item)
                    apply_yes_no(Extras.CASH_IN, item, location["filter_type"] == "1")
                yield item
