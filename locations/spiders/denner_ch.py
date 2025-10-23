from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class DennerCHSpider(Spider):
    name = "denner_ch"
    item_attributes = {"brand": "Denner", "brand_wikidata": "Q379911"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.denner.ch/api/store/list?page={page}",
            cb_kwargs={"current_page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: Response, current_page: int) -> Any:
        results = response.json()["data"]

        for location in results.get("hits", []):
            location.update(location.pop("_geo"))
            location["street-number"] = location.pop("number")
            location["street"] = location.pop("address")
            item = DictParser.parse(location)
            item.pop("name")
            item["website"] = response.urljoin(location["link"])
            opening_hours = (location.get("openingTimes") or {}).get("weeklyOpeningTimes", [])
            try:
                item["opening_hours"] = self.parse_opening_hours(opening_hours)
            except:
                self.logger.error(f"Failed to parse opening hours: {opening_hours}")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

        if current_page < results["totalPages"]:
            yield self.make_request(current_page + 1)

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if day := sanitise_day(rule.get("weekday"), DAYS_DE):
                hours_info = rule.get("statements")
                if hours_info[0]["info"] and hours_info[0]["info"][0].get("name") == "geschlossen":
                    oh.set_closed(day)
                else:
                    for shift in hours_info:
                        oh.add_range(day, shift["openFrom"], shift["openTo"])
        return oh
