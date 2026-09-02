import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT

# Field names used by the source for each day's opening hours, keyed to OSM day codes.
DAY_FIELDS = {"mo": "Mo", "tu": "Tu", "we": "We", "th": "Th", "fr": "Fr", "sa": "Sa", "so": "Su"}


class BankaustriaATSpider(Spider):
    name = "bankaustria_at"
    item_attributes = {"brand": "Bank Austria", "brand_wikidata": "Q697619"}
    start_urls = ["https://www.bankaustria.at/filialen/api/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location.get("Id")
            item["street_address"] = item.pop("street", None)
            item["phone"] = location.get("Telephone")
            item["email"] = (location.get("Email") or "").rstrip(";") or None
            item["website"] = "https://www.bankaustria.at/filialen/index.jsp"
            if fax := location.get("Fax"):
                if fax != "-":
                    item["extras"]["fax"] = fax

            if opening_hours := self.parse_hours(location):
                item["opening_hours"] = opening_hours

            features = location.get("Features") or ""
            apply_yes_no(Extras.ATM, item, "Geldausgabeautomat" in features)
            apply_yes_no(Extras.WHEELCHAIR, item, bool(location.get("AccessibleFeatures")))

            # "SB-Filiale" locations (Type 4) are unstaffed self-service foyers with no teller
            # desk ("Kassa"); tag these as an ATM rather than a bank branch.
            if location.get("Type") == "4" and "Kassa" not in features:
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)

            yield item

    def parse_hours(self, location: dict) -> OpeningHours | None:
        oh = OpeningHours()
        for field, day in DAY_FIELDS.items():
            hours = location.get(field)
            if not hours or hours == "Geschlossen":
                continue
            if m := re.match(r"(\d{1,2})\.(\d{2})\s*-\s*(\d{1,2})\.(\d{2})", hours):
                oh.add_range(day, "{}:{}".format(m.group(1), m.group(2)), "{}:{}".format(m.group(3), m.group(4)))
        return oh or None
