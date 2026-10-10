import re
from typing import Any, AsyncIterator, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

STATION_NAME_PATTERN = re.compile(r"^(\d+)\.\s*(.*)$")


class SeoulBikeKRSpider(Spider):
    name = "seoul_bike_kr"
    item_attributes = {
        "brand": "서울자전거 따릉이",
        "brand_wikidata": "Q28127084",
        "state": "서울특별시",
    }
    requires_proxy = "KR"  # Direct requests from foreign data-centre IPs are blocked.
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    async def start(self) -> AsyncIterator[Request]:
        # Visiting the main page establishes a JSESSIONID session cookie required by the WAF.
        yield Request("https://www.bikeseoul.com/main.do?lang=ko")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        yield FormRequest(
            url="https://www.bikeseoul.com/app/station/getStationRealtimeStatus.do",
            formdata={"stationGrpSeq": "ALL"},
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.bikeseoul.com/app/station/moveStationRealtimeStatus.do",
            },
            callback=self.parse_stations,
        )

    def parse_stations(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        stations = data.get("realtimeList", [])

        for station in stations:
            raw_name = station.get("stationName", "").strip()
            m = STATION_NAME_PATTERN.match(raw_name)
            if not m:
                continue

            station_num, station_name = m.groups()

            item = Feature()
            item["ref"] = station_num
            item["extras"]["ref:bikeseoul:id"] = station["stationId"]
            item["name"] = station_name.strip()
            item["lat"] = float(station["stationLatitude"])
            item["lon"] = float(station["stationLongitude"])
            item["website"] = "https://www.bikeseoul.com/"

            if rack_cnt := station.get("rackTotCnt"):
                item["extras"]["capacity"] = str(rack_cnt)

            apply_category(Categories.BICYCLE_RENTAL, item)

            yield item
