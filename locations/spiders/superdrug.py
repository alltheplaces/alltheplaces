from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST


class SuperdrugSpider(Spider):
    name = "superdrug"
    item_attributes = {"brand": "Superdrug", "brand_wikidata": "Q7643261"}
    user_agent = FIREFOX_LATEST
    custom_settings = {"DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"}}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://api.superdrug.com/api/v2/sd/stores?fields=FULL&pageSize=100&currentPage={}".format(page),
            headers={"Host": "api.superdrug.com"},
            callback=self.parse_api,
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            if location["address"]["country"]["isocode"] == "AZ":
                location["address"]["country"]["isocode"] = None  # Null island

            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["displayName"]
            item["street_address"] = merge_address_lines(
                [location["address"].get("line3"), location["address"].get("line2"), location["address"].get("line1")]
            )
            item["addr_full"] = location["address"]["formattedAddress"]
            item["website"] = urljoin("https://www.superdrug.com/", location["url"])
            item["phone"] = location["address"]["phone"]

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]["weekDayOpeningList"]:
                if rule["closed"] is True:
                    item["opening_hours"].set_closed(rule["weekDay"])
                else:
                    item["opening_hours"].add_range(
                        rule["weekDay"], rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"]
                    )
            apply_category(Categories.SHOP_CHEMIST, item)
            yield item

        pagination = response.json()["pagination"]
        if pagination["currentPage"] < pagination["totalPages"]:
            yield self.make_request(pagination["currentPage"] + 1)
