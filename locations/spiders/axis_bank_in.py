from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AxisBankINSpider(Spider):
    name = "axis_bank_in"
    item_attributes = {"brand": "Axis Bank", "brand_wikidata": "Q2003549"}
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_TIMEOUT": 300}

    def make_request(
        self, state: str, location_type: str, total_count: int, offset: int, limit: int = 3
    ) -> JsonRequest:
        return JsonRequest(
            url="https://j617xjxwjd.execute-api.ap-south-1.amazonaws.com/axis_bank_prod/getCmsData-V18",
            data={
                "functionName": "getHomeSearchResultElastic",
                "city": "",
                "searchType": "Advanced",
                "state": state,
                "cityAdvanceSearch": "",
                "location": "",
                "radius": "",
                "outletType": "",
                "searchCategory": [location_type],
                "searchService": [],
                "search": "",
                "offSet": offset,
                "pagesize": limit,
            },
            callback=self.parse_details,
            cb_kwargs=dict(
                state=state, location_type=location_type, offset=offset, limit=limit, total_count=total_count
            ),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://j617xjxwjd.execute-api.ap-south-1.amazonaws.com/axis_bank_prod/getCmsData-V18",
            data={
                "functionName": "getHomePageData",
                "searchType": "Advanced",
                "location": "",
                "cityAdvanceSearch": "",
                "state": "",
                "outletType": "",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_type in ["Branch", "ATM"]:
            for state in response.json()["state"]:
                yield self.make_request(state, location_type, 0, 0)

    def parse_details(
        self, response: Response, state: str, location_type: str, offset: int, limit: int, total_count: int
    ) -> Any:
        for location in response.json()["dealerData"]:
            location["latitude"] = location["latitude"].replace(", ", "")
            item = DictParser.parse(location)
            item["addr_full"] = location["complete_address"]
            item["branch"] = (
                location["dealerName"]
                .removeprefix("Axis Bank Branch")
                .removeprefix("Axis Bank ATM")
                .strip()
                .split(",")[0]
            )
            item["website"] = "/".join(["https://branch.axisbank.com", location["seoSlug"], "Home"])
            item["postcode"] = location["pin_code"]
            item["opening_hours"] = OpeningHours()
            if location["openHr"] == "Open 24 hours":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"].add_ranges_from_string(location["openHr"].replace("|", "-"))
            if location["category"] == "Branch":
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
            yield item

        new_offset = offset + limit
        total_count = total_count or response.json()["totalCount"]
        if new_offset < total_count:
            yield self.make_request(state, location_type, total_count, new_offset)
