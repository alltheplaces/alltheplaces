from typing import Any, Iterable

import chompjs
import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.obi_eu import OBI_SHARED_ATTRIBUTES


class ObiRUSpider(scrapy.Spider):
    name = "obi_ru"
    item_attributes = OBI_SHARED_ATTRIBUTES
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://obi.ru/graphql",
            data={
                "query": """
                  query OfflineStores {
                    offlineStores {
                        cash_register_description
                        city
                        description
                        email
                        enabled
                        fax
                        frontend_description
                        is_central
                        is_pickup_location_active
                        latitude
                        longitude
                        name
                        phone
                        postcode
                        region
                        region_id
                        schedule
                        source_code
                        street
                        url_key
                    }
                }
                """,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # HTML response contains JSON data
        for store in chompjs.parse_js_object(response.text)["data"]["offlineStores"]:
            if any(keyword in store["name"] for keyword in ["Тест", "Default"]):
                continue  # Exclude test POIs
            if "не работает" in store["schedule"]:  # not operating
                continue
            item = DictParser.parse(store)
            item["ref"] = store.get("source_code")
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").removeprefix("ОБИ ")
            item["phone"] = item["phone"].split("доб")[0] if item.get("phone") else None
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                store.get("schedule"), DAYS_RU, NAMED_DAY_RANGES_RU, NAMED_TIMES_RU
            )
            yield item
