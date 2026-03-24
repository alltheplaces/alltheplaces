from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST


class LietuvosPastasLTSpider(Spider):
    name = "lietuvos_pastas_lt"
    item_attributes = {"operator": "Lietuvos paštas", "operator_wikidata": "Q175964"}
    custom_settings = {
        "DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"},
        "USER_AGENT": FIREFOX_LATEST,
    }

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            "https://post.lt/post/codes/search/getPlaces",
            headers={"X-Requested-With": "XMLHttpRequest"},
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
