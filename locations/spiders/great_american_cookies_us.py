from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class GreatAmericanCookiesUSSpider(Spider):
    name = "great_american_cookies_us"
    item_attributes = {
        "brand_wikidata": "Q5598629",
        "brand": "Great American Cookies",
    }

    async def start(self):
        yield JsonRequest(
            url="https://ordernew-admin.greatamericancookies.com/api/v1/restaurants/", headers={"projectid": "1"}
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_id in response.json():
            yield JsonRequest(
                url=f"https://ordernew-admin.greatamericancookies.com/api/v1/restaurants/{location_id['id']}",
                headers={"projectid": "1"},
                callback=self.parse_details,
            )

    def parse_details(self, response: Response):
        data = response.json()
        if data:
            data.update(data.pop("address"))
            item = DictParser.parse(data)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["website"] = "https://ordernew.greatamericancookies.com/gac/" + data["location_slug"]
            yield item
