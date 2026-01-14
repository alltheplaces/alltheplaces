from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class TelenorNOSpider(Spider):
    name = "telenor_no"
    allowed_domains = ["store.telenor.no"]
    item_attributes = {
        "brand": "Telenorbutikken",
        "brand_wikidata": "Q845632",
        "country": "NO",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://store.telenor.no/omnichannel/v1/dealers/search?isConsumer=true&limit=100")

    def parse(self, response) -> Iterable[Feature]:
        for store in response.json():
            item = DictParser.parse(store)

            # Prefer storeId over id for ref
            item["ref"] = store.get("storeId") or store.get("id")

            # Get branch name by removing common store prefix
            item["branch"] = store.get("name").removeprefix("Telenorbutikken ").strip()

            # Add city and shopping centre info
            if address := store.get("address"):
                item["city"] = address.get("postalArea")
                if shopping_centre := address.get("shoppingCentre"):
                    item["located_in"] = shopping_centre

            # Get website URL based on normalized store name
            if name := item.get("name"):
                slug = name.casefold()
                slug = slug.removeprefix("telenorbutikken").strip()
                slug = slug.translate(str.maketrans({"ø": "o", "æ": "ae", "å": "aa"}))
                slug = "-".join(slug.split())
                item["website"] = f"https://www.telenor.no/telenorbutikken/{slug}"

            # Get and format opening hours
            if opening_hours := store.get("openingHours"):
                oh = OpeningHours()

                if week_days := opening_hours.get("weekDays"):
                    opening_time = week_days.get("openingTime")
                    closing_time = week_days.get("closingTime")
                    if opening_time and closing_time:
                        oh.add_days_range(DAYS_WEEKDAY, opening_time.replace(".", ":"), closing_time.replace(".", ":"))

                if saturday := opening_hours.get("saturday"):
                    opening_time = saturday.get("openingTime")
                    closing_time = saturday.get("closingTime")
                    if opening_time and closing_time:
                        oh.add_range("Sa", opening_time.replace(".", ":"), closing_time.replace(".", ":"))

                item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item
