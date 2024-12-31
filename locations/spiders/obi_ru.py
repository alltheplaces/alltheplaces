from typing import Any, Iterable

import chompjs
import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
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
            if "Тест" in store["name"] or "Default" in store["name"]:
                continue  # Exclude test POIs
            item = DictParser.parse(store)
            item["ref"] = store.get("source_code")
            item["street_address"] = item.pop("street")
            yield item
