import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class PoltronesofaSpider(Spider):
    name = "poltronesofa"
    item_attributes = {"brand": "Poltronesofà", "brand_wikidata": "Q80833069"}
    start_urls = ["https://www.poltronesofa.com/api/stores?locale=fr-FR&limit=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]["data"]:
            location = store["attributes"]
            # The store finder only shows stores with Google Business Profile data
            if not location["GMBtitle"] or location["GMBstoreStatus"] == "Fermé définitivement":
                continue

            item = Feature()
            item["ref"] = store["id"]
            item["branch"] = location["GMBtitle"]
            item["lat"] = location["GMBlatitude"]
            item["lon"] = location["GMBlongitude"]
            item["phone"] = location["GMBphoneNumber"]
            item["country"] = location["GMBcountry"]
            item["addr_full"] = location["GMBaddress"]
            if m := re.search(r"^(.+?),\s*([\d ]+?)\s*-\s*([^,]+)$", location["GMBaddress"]):
                item["street_address"], item["postcode"], item["city"] = m.groups()
            item["opening_hours"] = self.parse_opening_hours((location["Geo"] or {}).get("OpeningDays"))
            apply_category(Categories.SHOP_FURNITURE, item)
            yield item

    @staticmethod
    def parse_opening_hours(text: str | None) -> OpeningHours | None:
        if not text:
            return None
        oh = OpeningHours()
        for line in text.strip().splitlines():
            if not (m := re.match(r"(?:du\s+)?(.+?)\s+(ferm[ée]|\d.*)$", line.strip(), re.IGNORECASE)):
                return None
            days_text, times = m.groups()
            rng = re.fullmatch(r"(\w+)\s+au\s+(\w+)", days_text)
            days = [
                sanitise_day(day, DAYS_FR) for day in (rng.groups() if rng else re.split(r",\s*|\s+et\s+", days_text))
            ]
            if None in days:
                return None
            if rng:
                days = day_range(*days)
            if times.lower().startswith("ferm"):
                oh.set_closed(days)
                continue
            for period in times.split("/"):
                if not (
                    t := re.fullmatch(r"(\d{1,2})(?:[:h.](\d{2})?)?\s*-\s*(\d{1,2})(?:[:h.](\d{2})?)?", period.strip())
                ):
                    return None
                h1, m1, h2, m2 = t.groups()
                oh.add_days_range(days, f"{h1}:{m1 or '00'}", f"{h2}:{m2 or '00'}")
        return oh
