from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class BurgerKingRUSpider(PlaywrightSpider):
    name = "burger_king_ru"
    item_attributes = {"brand": "Бургер Кинг", "brand_wikidata": "Q177054"}
    allowed_domains = ["orderapp.burgerkingrus.ru"]
    api_url = "https://orderapp.burgerkingrus.ru/gateway/restaurant-composition/api/v7/restaurants/search?lon=37.621202&lat=55.753544&limit=2000"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self.api_url, cookies={"spid": "", "spsc": ""})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("name", None)
            item["city"] = location["city"]["city_name"]
            item["phone"] = None  # A single national number, varying only by extension
            try:
                item["opening_hours"] = self.parse_opening_hours(location.get("timetable", []))
            except Exception as e:
                self.logger.error(f'Failed to parse opening hours:{location.get("timetable", [])} {e}')

            if location.get("features"):
                apply_yes_no(Extras.DRIVE_THROUGH, item, location["features"].get("king_drive") is True, False)

            apply_category(Categories.FAST_FOOD, item)
            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for day_number, day_name in enumerate(DAYS):
            day_hours = rules[day_number]
            if not day_hours["active"]:
                opening_hours.set_closed(day_name)
                continue
            opening_hours.add_range(day_name, day_hours["time_from"], day_hours["time_to"])
        return opening_hours
