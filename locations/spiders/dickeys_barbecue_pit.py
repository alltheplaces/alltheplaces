from typing import Any, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class DickeysBarbecuePitSpider(Spider):
    name = "dickeys_barbecue_pit"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    COUNTRY_WEBSITE_MAP = {
        "US": "https://www.dickeys.com/locations",
        "CA": "https://www.dickeys.com/ca/en-ca/locations",
    }
    build_id = ""

    def start_requests(self) -> Iterable[Request]:
        for country in self.COUNTRY_WEBSITE_MAP.keys():
            yield Request(url=self.COUNTRY_WEBSITE_MAP[country], cb_kwargs={"country": country})

    def parse(self, response: Response, country: str) -> Any:
        location_data = chompjs.parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        self.build_id = location_data.get("buildId")
        api_url = f"https://www.dickeys.com/_next/data/{self.build_id}/locations"
        if "/ca/" in response.url:
            api_url = api_url.replace("/locations", "/ca/en-ca/locations")
        for state_info in location_data["props"]["pageProps"]["locations"]:
            for state in state_info["states"]:
                state = state["stateName"].lower()
                yield JsonRequest(
                    url=f"{api_url}/{state}.json".replace(" ", "-"),
                    callback=self.parse_cities,
                    meta={"website": response.url, "state": state, "country": country},
                )

    def parse_cities(self, response: Response, **kwargs: Any) -> Any:
        for city_info in response.json()["pageProps"]["stateCities"]:
            yield JsonRequest(
                url=response.url.replace(".json", f"/{city_info['city'].lower()}.json").replace(" ", "-"),
                callback=self.parse_stores,
                meta=response.meta,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["pageProps"]["data"]["locations"]:
            store.update(store.pop("address"))
            store["state"] = store.pop("state", {}).get("abbreviation")
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["addr_full"] = store.get("fullAddress")
            item["branch"] = store.get("label")
            item["website"] = (
                f'{response.meta["website"]}/{response.meta["state"]}/{item["city"].lower()}/{store["slug"]}'.replace(
                    " ", "-"
                )
            )
            item["country"] = response.meta["country"]
            item["opening_hours"] = OpeningHours()
            for rule in store.get("workingHours", []):
                if day := sanitise_day(rule.get("label")):
                    item["opening_hours"].add_range(day, rule.get("opened"), rule.get("closed"), time_format="%I:%M %p")
            yield item
