from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class BaylorScottWhiteHealthUSSpider(Spider):
    name = "baylor_scott_white_health_us"
    item_attributes = {"operator": "Baylor Scott & White Health", "operator_wikidata": "Q41568258"}
    allowed_domains = ["phyndapi.bswapi.com"]
    base_url = "https://phyndapi.bswapi.com/V4/Places/GetLocations"
    headers = {
        "x-bsw-clientid": "BSWHealth.com",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.base_url + "?perPage=1",
            headers=self.headers,
            callback=self.get_pages,
        )

    def get_pages(self, response: Response) -> Iterable[JsonRequest]:
        total_count = response.json()["locationCount"]
        page_number = 0
        page_size = 100

        while page_number * page_size < total_count:
            yield JsonRequest(
                self.base_url + f"?perPage={page_size}&pageNumber={page_number + 1}", headers=self.headers
            )
            page_number += 1

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in response.json()["locationResults"]:
            properties = {
                "ref": row["locationID"],
                "name": row["locationName"],
                "street_address": clean_address([row["locationStreet1"], row.get("locationStreet2", "")]),
                "city": row["locationCity"],
                "postcode": row["locationZip"],
                "state": row["locationState"],
                "lat": row["coordinates"]["lat"],
                "lon": row["coordinates"]["lon"],
                "phone": row["locationPhone"].replace(".", " "),
                "website": row["locationUrl"],
                "image": row["photoUrl"],
            }

            oh = OpeningHours()
            for day in row["dailyHours"]:
                oh.add_range(
                    day["weekDayName"][:2],
                    day["openingTime"],
                    day["closingTime"],
                    "%H:%M:%S",
                )

            properties["opening_hours"] = oh

            yield Feature(**properties)
