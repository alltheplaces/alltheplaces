from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class DickeysBarbecuePitUSSpider(Spider):
    name = "dickeys_barbecue_pit_us"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    start_urls = ["https://www.dickeys.com/locations"]
    build_id = ""

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_data = chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        self.build_id = location_data.get("buildId")
        for state_info in location_data["props"]["pageProps"]["locations"][0]["states"]:
            state = state_info["stateName"].lower()
            yield JsonRequest(
                url=f"https://www.dickeys.com/_next/data/{self.build_id}/locations/{state}.json".replace(" ", "-"),
                callback=self.parse_cities,
                cb_kwargs=dict(state=state),
            )

    def parse_cities(self, response: Response, state: str) -> Any:
        for city_info in response.json()["pageProps"]["stateCities"]:
            yield JsonRequest(
                url=f"https://www.dickeys.com/_next/data/{self.build_id}/locations/{state}/{city_info['city'].lower()}.json".replace(
                    " ", "-"
                ),
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["pageProps"]["data"]["locations"]:
            store.update(store.pop("address"))
            store["state"] = store.pop("state", {}).get("abbreviation")
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["addr_full"] = store.get("fullAddress")
            yield item
