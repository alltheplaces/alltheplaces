from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import NAMED_DAY_RANGES_EN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class FixPriceSpider(Spider):
    name = "fix_price"
    item_attributes = {"brand": "Fix Price", "brand_wikidata": "Q4038791"}
    allowed_domains = ["api.fix-price.com"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            "https://api.fix-price.com/buyer/v1/location/country",
            callback=self.fetch_pois_for_country,
            dont_filter=True,
        )

    def fetch_pois_for_country(self, response: Response) -> Iterable[JsonRequest]:
        for country in response.json():
            for filters in ["canPickup=all&showTemporarilyClosed=all", "showTemporarilyClosed=all"]:
                yield JsonRequest(f'https://api.fix-price.com/buyer/v1/store?countryId={country["id"]}&{filters}')

    def parse(self, response: Response) -> Iterable[Feature]:
        for poi in response.json():
            if not poi.get("isActive"):
                continue
            item = DictParser.parse(poi)
            apply_yes_no(Extras.DELIVERY, item, poi.get("canPickup"))
            apply_yes_no(PaymentMethods.CARDS, item, poi.get("canPayCard"))
            apply_category(Categories.SHOP_VARIETY_STORE, item)
            self.parse_hours(item, poi)
            yield item

    def parse_hours(self, item: Feature, poi: dict) -> None:
        schedule_data = {
            "Weekdays": poi.get("scheduleWeekdays"),
            "Sa": poi.get("scheduleSaturday"),
            "Su": poi.get("scheduleSunday"),
        }
        try:
            oh = OpeningHours()
            for day, schedule in schedule_data.items():
                if schedule:
                    open, close = schedule.split("-")
                    oh.add_days_range(NAMED_DAY_RANGES_EN[day] if day == "Weekdays" else [day], open, close)
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {schedule_data}, {e}")
