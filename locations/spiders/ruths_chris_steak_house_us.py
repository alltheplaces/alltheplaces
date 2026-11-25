from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours, day_range
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class RuthsChrisSteakHouseUSSpider(Spider):
    name = "ruths_chris_steak_house_us"
    item_attributes = {"brand": "Ruth's Chris Steak House", "brand_wikidata": "Q7382829", "country": "US"}
    allowed_domains = ["www.ruthschris.com"]
    start_urls = ["https://www.ruthschris.com/locations-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        self.urls = {}
        for url in iterloc(Sitemap(response.body)):
            self.urls[url.rstrip("/").rsplit("/", 1)[-1]] = url

        yield JsonRequest(
            url="https://www.ruthschris.com/api/restaurants",
            headers={"x-source-channel": "WEB"},
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["restaurants"]:
            location.update(location["contactDetail"].pop("address", {}))
            if location.get("country") != "US":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["branch"] = location["restaurantName"]
            item["phone"] = self.parse_phone(location)
            item["street_address"] = merge_address_lines([location.get("street1"), location.get("street2")])
            item["website"] = self.urls.get(str(item["ref"]))
            item["opening_hours"] = self.parse_hours(location)
            item["extras"]["cuisine"] = "american;steak_house"
            apply_category(Categories.RESTAURANT, item)

            yield item

    @staticmethod
    def parse_phone(location: dict) -> str | None:
        if phones := location.get("contactDetail", {}).get("phoneDetail"):
            return phones[0].get("phoneNumber")
        return None

    @staticmethod
    def parse_hours(location: dict) -> OpeningHours | None:
        opening_hours = OpeningHours()
        for day in location.get("restaurantHours", []):
            if day.get("isRestaurantClosed") and day.get("day"):
                opening_hours.set_closed(day["day"])
                continue

            for hours_info in day.get("hoursInfo", []):
                if hours_info.get("name") == "Hours of Operations":
                    if day.get("day"):
                        opening_hours.add_range(
                            day=day["day"],
                            open_time=hours_info["startTime"],
                            close_time=hours_info["endTime"],
                            time_format="%I:%M %p",
                        )
                    elif hours_info.get("dayOfWeek") and hours_info.get("endDayOfWeek"):
                        start_day = DAYS_FULL[hours_info["dayOfWeek"] - 1]
                        end_day = DAYS_FULL[hours_info["endDayOfWeek"] - 1]
                        opening_hours.add_days_range(
                            day_range(start_day, end_day),
                            open_time=hours_info["startTime"],
                            close_time=hours_info["endTime"],
                            time_format="%I:%M %p",
                        )

        return opening_hours if opening_hours.as_opening_hours() else None
