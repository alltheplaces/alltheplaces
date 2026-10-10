import html
import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page links to a listing per state, and each listing hides its
# restaurants in a "storeList" input as JSON, with coordinates, phone and
# hours. The listing covers other countries too, so only the US restaurants
# are kept.
#
# Hours are HTML with non breaking spaces, e.g.
# "Monday - Sunday:&nbsp;11&nbsp;am&nbsp;-&nbsp;9&nbsp;pm".


class FamousDavesUSSpider(Spider):
    name = "famous_daves_us"
    item_attributes = {"brand": "Famous Dave's", "brand_wikidata": "Q5433448"}
    allowed_domains = ["www.famousdaves.com"]
    start_urls = ["https://www.famousdaves.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for path in set(response.xpath('//a[contains(@href, "/Locations/List")]/@href').getall()):
            yield response.follow(path, callback=self.parse_state)

    def parse_state(self, response: Response) -> Iterable[Feature]:
        if not (store_list := response.xpath('//input[@id="storeList"]/@value').get()):
            return

        for location in json.loads(store_list):
            # The locator also covers franchises in the UAE and elsewhere.
            if (location.get("Country") or "").upper() not in ["USA", "US"]:
                continue

            item = Feature()
            item["ref"] = location.get("StoreNumber") or location["Id"]
            item["branch"] = location.get("Name")
            item["lat"] = location.get("Latitude")
            item["lon"] = location.get("Longitude")
            item["street_address"] = location.get("AddressLine1")
            item["city"] = location.get("City")
            item["state"] = location.get("StateCode")
            item["phone"] = location.get("PhoneNumber")
            item["operator"] = location.get("Operator")
            if restaurant := location.get("RestaurantUrl"):
                item["website"] = response.urljoin(f"/Locations/{restaurant}")

            # "Apple Valley, MN 55124"
            if postcode := re.search(r"\b(\d{5})\b", location.get("AddressLine2") or ""):
                item["postcode"] = postcode.group(1)

            item["opening_hours"] = self.parse_opening_hours(location.get("Hours") or "")

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "barbecue"

            yield item

    @staticmethod
    def parse_opening_hours(hours: str) -> OpeningHours | None:
        """Parses "Monday - Sunday:&nbsp;11&nbsp;am&nbsp;-&nbsp;9&nbsp;pm"."""
        oh = OpeningHours()

        text = re.sub(r"<[^>]+>", " ", html.unescape(hours)).replace("\xa0", " ")
        text = re.sub(r"\s+", " ", text).replace("\u2013", "-").replace("\u2014", "-")

        # Rules run together with no separator, e.g. "Monday-Thursday: 11 am -
        # 9 pm Friday-Saturday: 11 am - 10 pm", and the day and times are
        # divided by a colon, a dash or nothing at all.
        for days, open_time, open_meridiem, close_time, close_meridiem in re.findall(
            r"([A-Za-z][A-Za-z &,]*(?:\s*-\s*[A-Za-z]+)?)\s*[:\-]?\s*"
            r"(\d{1,2}(?::\d{2})?)\s*([ap]m)?\s*-\s*(\d{1,2}(?::\d{2})?)\s*([ap]m)",
            text,
            re.I,
        ):
            day_names = []
            for token in re.split(r"&|,|\band\b", days):
                token = token.strip()
                if "-" in token:
                    start, end = [sanitise_day(part) for part in token.split("-", 1)]
                    if start and end:
                        day_names.extend(day_range(start, end))
                elif day := sanitise_day(token):
                    day_names.append(day)

            if not day_names:
                continue

            oh.add_days_range(
                day_names,
                FamousDavesUSSpider.normalise_time(open_time, open_meridiem or close_meridiem),
                FamousDavesUSSpider.normalise_time(close_time, close_meridiem),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str, meridiem: str) -> str:
        value = value if ":" in value else f"{value}:00"
        return f"{value}{meridiem.upper()}"
