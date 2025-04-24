from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SdekSpider(scrapy.Spider):
    name = "sdek"
    allowed_domains = ["www.cdek.ru"]
    item_attributes = {"brand": "СДЭК", "brand_wikidata": "Q28665980", "extras": {"brand:en": "SDEK"}}
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    # Because of bot detection after certain no. of requests querying GraphQL API https://www.cdek.ru/api-site/v1/graphql/ for individual POI details is no longer feasible.
    def make_request(self, page: int, limit: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.cdek.ru/api-site/website/office/?locale=ru&coords[startLat]=-90&coords[startLong]=-180&coords[endLat]=90&coords[endLong]=180&limit={limit}&page={page}",
            meta={"page": page},
            dont_filter=True,
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json().get("data", {}).get("data", []):
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full")
            item["ref"] = poi.get("code")
            item["website"] = f'https://www.cdek.ru/ru/offices/view/{item["ref"]}/'
            item["lat"] = poi.get("geoLatitude")
            item["lon"] = poi.get("geoLongitude")

            category = poi.get("type")
            if category == "PVZ":
                apply_category(Categories.POST_OFFICE, item)
            elif category == "POSTAMAT":
                apply_category(Categories.PARCEL_LOCKER, item)
                apply_yes_no("parcel_mail_in", item, poi.get("isReception"))
                apply_yes_no("parcel_pickup", item, poi.get("isHangout"))
            self.parse_hours(item, poi)
            yield item

        if response.json()["data"]["count"] == 100:
            yield self.make_request(response.meta["page"] + 1)

    def parse_hours(self, item: Feature, poi: dict) -> Any:
        if hours := poi.get("worktimes"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    oh.add_range(
                        day=DAYS[hour["day"] - 1],
                        open_time=hour["startTime"],
                        close_time=hour["stopTime"],
                        time_format="%H:%M:%S",
                    )
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {hours}, {e}")
