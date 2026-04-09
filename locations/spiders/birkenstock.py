import html
import json
import re
from typing import AsyncIterator, Generator

import scrapy
from scrapy.http import JsonRequest, Request, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class BirkenstockSpider(scrapy.Spider):
    name = "birkenstock"
    item_attributes = {
        "brand": "Birkenstock",
        "brand_wikidata": "Q648458",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    # Countries with their storesresult URL path prefix and a representative lat/lng.
    # Each entry is scoped to that country by the Birkenstock backend.
    COUNTRIES = [
        # US
        ("us", 39.5, -98.35),
        # EU countries (Sites-EU-Site, each scoped to its country)
        ("at", 47.5162, 14.5501),
        ("be", 50.5039, 4.4699),
        ("ch", 46.8182, 8.2275),
        ("cz-en", 49.8175, 15.473),
        ("de", 51.1657, 10.4515),
        ("dk", 56.2639, 9.5018),
        ("es", 40.4637, -3.7492),
        ("fi-en", 61.9241, 25.7482),
        ("fr", 46.2276, 2.2137),
        ("gb", 55.3781, -3.436),
        ("gr-en", 39.0742, 21.8243),
        ("hr-en", 45.1, 15.2),
        ("hu", 47.1625, 19.5033),
        ("ie", 53.4129, -8.2439),
        ("it", 41.8719, 12.5674),
        ("lu", 49.8153, 6.1296),
        ("nl", 52.1326, 5.2913),
        ("no", 60.472, 8.4689),
        ("pl", 51.9194, 19.1451),
        ("pt", 39.3999, -8.2245),
        ("se", 60.1282, 18.6435),
        # Japan
        ("jp", 36.2048, 138.2529),
        # Korea
        ("kr", 37.5665, 126.978),
        # Middle East & Africa
        ("ae", 23.4241, 53.8478),
        ("bh", 26.0275, 50.55),
        ("kw", 29.3759, 47.9774),
        ("om", 21.5129, 55.9233),
        ("qa", 25.3548, 51.1839),
        ("sa", 23.8859, 45.0792),
        # Southeast Asia
        ("hk", 22.3193, 114.1694),
        ("my", 4.2105, 101.9758),
        ("ph", 12.8797, 121.774),
        ("sg", 1.3521, 103.8198),
    ]

    async def start(self) -> AsyncIterator[Request]:
        # Make initial request to storesresult to discover the FilterStores URL
        # (which encodes the correct SFCC site ID and locale for each country).
        for country_path, lat, lng in self.COUNTRIES:
            url = (
                f"https://www.birkenstock.com/{country_path}/storesresult/"
                f"?lat={lat}&lng={lng}&storeLocatorType=2&ajax=true"
            )
            yield Request(
                url=url,
                callback=self.parse_storesresult,
                cb_kwargs={"lat": lat, "lng": lng},
            )

    def parse_storesresult(self, response: Response, lat: float, lng: float) -> Generator:
        # Extract the stores model to get the filterStoresLink for this country's SFCC site
        match = re.search(r'data-stores-model="([^"]+)"', response.text)
        if not match:
            return

        stores_model_raw = html.unescape(match.group(1))
        if stores_model_raw == "null":
            return

        stores_model = json.loads(stores_model_raw)

        # Use filterStoresLink to make a filtered request for storeType=1 (Birkenstock stores)
        filter_stores_path = stores_model.get("filterStoresLink")
        if not filter_stores_path:
            return

        filter_url = f"https://www.birkenstock.com{filter_stores_path}&storeType=1&ajax=true"
        yield JsonRequest(
            url=filter_url,
            callback=self.parse_filter_stores,
            cb_kwargs={"lat": lat, "lng": lng},
        )

    def parse_filter_stores(self, response: Response, lat: float, lng: float) -> Generator:
        data = response.json()
        stores_model = data.get("storesModel", {})

        yield from self._yield_stores(stores_model)

        if stores_model.get("isLoadMoreButtonEnabled"):
            more_list_path = stores_model.get("loadMoreButtonLink")
            if more_list_path:
                yield from self._request_more(more_list_path, lat, lng, page=2)

    def parse_more_list(self, response: Response, lat: float, lng: float, more_list_path: str, page: int) -> Generator:
        data = response.json()
        stores_model = data.get("storesModel", {})

        yield from self._yield_stores(stores_model)

        if stores_model.get("isLoadMoreButtonEnabled"):
            yield from self._request_more(more_list_path, lat, lng, page=page + 1)

    def _request_more(self, more_list_path: str, lat: float, lng: float, page: int) -> Generator:
        url = (
            f"https://www.birkenstock.com{more_list_path}"
            f"?lat={lat}&lng={lng}&storeLocatorType=2&storeType=1&pageNumber={page}&ajax=true"
        )
        yield JsonRequest(
            url=url,
            callback=self.parse_more_list,
            cb_kwargs={"lat": lat, "lng": lng, "more_list_path": more_list_path, "page": page},
        )

    def _yield_stores(self, stores_model: dict) -> Generator[Feature, None, None]:
        for store in stores_model.get("stores", []):
            item = DictParser.parse(store)

            # stateCode is not auto-mapped by DictParser (region_keys doesn't include it)
            if store.get("stateCode"):
                item["state"] = store["stateCode"]

            store_detail = store.get("storeDetailLink", "")
            item["website"] = "https://www.birkenstock.com" + store_detail.split("#")[0]

            yield item
