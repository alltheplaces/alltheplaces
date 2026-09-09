from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids, vincenty_distance
from locations.user_agents import BROWSER_DEFAULT

API_URL = "https://www.oliveyoung.co.kr/oystore/api/storeFinder/find-store"
STORE_FINDER_URL = "https://www.oliveyoung.co.kr/store/store/getStoreInfoMain.do"
HEADERS = {
    "Accept": "application/json",
    "Origin": "https://www.oliveyoung.co.kr",
    "Referer": STORE_FINDER_URL,
    "X-Requested-With": "XMLHttpRequest",
}
CENTROID_OFFSET_BEARINGS = (45, 135, 225, 315)


class OliveYoungKRSpider(Spider):
    name = "olive_young_kr"
    item_attributes = {"brand_wikidata": "Q55643246"}
    allowed_domains = ["www.oliveyoung.co.kr"]
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 2,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    requires_proxy = "KR"  # Cloudflare blocks direct requests from data-centre IPs.

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The API has a fixed 20 km radius, but ATP's smallest country grid has
        # a 24 km covering radius. Four searches offset 12 km from each grid
        # centroid cover the original cell without leaving gaps.
        for lat, lon in country_iseadgg_centroids("KR", 24):
            for bearing in CENTROID_OFFSET_BEARINGS:
                search_lat, search_lon = vincenty_distance(lat, lon, 12, bearing)
                yield self.store_request(search_lat, search_lon, 1)

    def store_request(self, lat: float, lon: float, page_idx: int) -> JsonRequest:
        # All coordinate fields are required by the API, even though the map
        # and search coordinates have the same values for a location search.
        return JsonRequest(
            API_URL,
            data={
                "lat": lat,
                "lon": lon,
                "pageIdx": page_idx,
                "searchWords": "",
                "pogKeys": "",
                "serviceKeys": "",
                "mapLat": lat,
                "mapLon": lon,
            },
            headers=HEADERS,
            cb_kwargs={"lat": lat, "lon": lon, "page_idx": page_idx},
        )

    def parse(self, response: Response, lat: float, lon: float, page_idx: int, **kwargs: Any) -> Any:
        data = response.json()["data"]
        stores = data["storeList"]
        for store in stores:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("올리브영").strip()

            address_parts = item["addr_full"].split(maxsplit=2)
            if address_parts:
                item["state"] = address_parts[0]
            if len(address_parts) > 1 and address_parts[1].endswith(("시", "군", "구")):
                item["city"] = address_parts[1]

            yield item

        # totalCount is the count for this page, not the total result count.
        # Page 11 is empty, so continue until an empty page or the known cap.
        if stores and page_idx < 10:
            yield self.store_request(lat, lon, page_idx + 1)
