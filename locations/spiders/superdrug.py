import json
from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import FIREFOX_LATEST


class SuperdrugSpider(PlaywrightSpider):
    name = "superdrug"
    item_attributes = {"brand": "Superdrug", "brand_wikidata": "Q7643261"}
    custom_settings = {
        "DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"},
        "USER_AGENT": FIREFOX_LATEST,
    } | DEFAULT_PLAYWRIGHT_SETTINGS

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            "https://api.superdrug.com/api/v2/sd/stores?fields=FULL&pageSize=100&currentPage={}".format(page),
            headers={"Host": "api.superdrug.com"},
            callback=self.parse_api,
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        results = json.loads(response.xpath("//pre/text()").get())
        for location in results["stores"]:
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
            item["phone"] = location["address"].get("phone")

            item["opening_hours"] = self.parse_opening_hours(location["openingHours"]["weekDayOpeningList"])

            apply_category(Categories.SHOP_CHEMIST, item)
            yield item

        pagination = results["pagination"]
        if pagination["currentPage"] < pagination["totalPages"]:
            yield self.make_request(pagination["currentPage"] + 1)

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            if (
                rule["closed"] is True
                or rule["openingTime"]["formattedHour"] == rule["closingTime"]["formattedHour"] == "00:00"
            ):
                opening_hours.set_closed(rule["weekDay"])
            else:
                opening_hours.add_range(
                    rule["weekDay"], rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"]
                )
        return opening_hours
