from typing import Any, AsyncIterator

from scrapy import FormRequest
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import CHROME_LATEST


class LietuvosPastasLTSpider(PlaywrightSpider):
    name = "lietuvos_pastas_lt"
    item_attributes = {"operator": "Lietuvos paštas", "operator_wikidata": "Q175964"}
    drop_attributes = {"phone", "email"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            "https://post.lt/post/codes/search/getPlaces",
            headers={"X-Requested-With": "XMLHttpRequest", "user-agent": CHROME_LATEST},
            formdata={"municipality": "0", "city": "", "street": "", "la": "", "lo": ""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["housenumber"] = location["addressDetails"]["houseNumber"]
            item["street"] = location["addressDetails"]["streetName"]
            item["postcode"] = location["addressDetails"]["postCode"]
            item["city"] = location["addressDetails"]["settlementName"]
            item["lat"] = location["map"]["latitude"]
            item["lon"] = location["map"]["longitude"]
            if location["type"] == "MobilePostBox":
                continue
            elif location["type"] == "PostBox":
                apply_category(Categories.POST_BOX, item)
                item["name"] = None
            elif location["type"] == "PostOffice":
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] == "PostTerminal":
                apply_category(Categories.PARCEL_LOCKER, item)

            yield item
