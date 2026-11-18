import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CaltexSpider(Spider):
    name = "caltex"
    item_attributes = {"brand": "Caltex", "brand_wikidata": "Q277470"}
    allowed_domains = ["www.caltex.com"]
    start_urls = [
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/au/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/hk/en/find-a-caltex-station&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/my/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/pk/en/find-us/locators&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/ph/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/sg/en/find-a-caltex-station&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/th/th/find-us&siteType=b2c",
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    @staticmethod
    def parse_au_opening_hours(text: str | None) -> OpeningHours | str | None:
        """Parse the free text `operatingHours` of an Australian station; None unless it is read in full."""
        text = " ".join((text or "").split())
        lower = text.lower()
        if re.fullmatch(r"(daily )?24 hours?", lower):
            return "24/7"
        # Times without am/pm, or any word other than days, "daily" and "closed", are not read.
        leftover = re.sub(r"\d{1,2}(?:[:.]\d{2})?\s*[ap]m", " ", lower)
        leftover = re.sub(
            r"\b(?:mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:r(?:s(?:day)?)?)?|fri(?:day)?|sat(?:urday)?"
            r"|sun(?:day)?|daily|closed|to|and)\b|[-–&,.;:]",
            " ",
            leftover,
        )
        if re.search(r"[a-z0-9]", leftover):
            return None
        text = re.sub(r"\bsat\s*&\s*sun\b", "Sat-Sun", text, flags=re.IGNORECASE)
        results = OpeningHours.extract_hours_from_string(text)
        if not results or len(results) != len(re.findall(r"[ap]m\s*(?:-|–|to)\s*\d|closed", text, flags=re.IGNORECASE)):
            return None
        oh = OpeningHours()
        for days, open_time, close_time in results:
            for day in days:
                if open_time == "closed":
                    oh.set_closed(day)
                else:
                    oh.add_range(day, open_time, close_time)
        return oh or None

    def parse(self, response):
        for location in response.json():
            if location["siteType"] != "Station":
                continue

            item = DictParser.parse(location)

            if location.get("fuelsName"):
                apply_yes_no(
                    Fuel.OCTANE_98,
                    item,
                    "PULP 98" in location["fuelsName"]
                    or (
                        "/hk/" in response.url
                        and (
                            "Gold with Techron Gasoline" in location["fuelsName"]
                            or "Platinum with Techron Gasoline" in location["fuelsName"]
                        )
                    )
                    or "Platinum 98 with Techron" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.OCTANE_97, item, "Premium 97" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.OCTANE_95,
                    item,
                    "PULP 95" in location["fuelsName"]
                    or "Premium 95" in location["fuelsName"]
                    or ("/ph/" in response.url and "Platinum with Techron" in location["fuelsName"])
                    or "Platinum with Techron Gasoline" in location["fuelsName"]
                    or "Premium 95 with Techron" in location["fuelsName"]
                    or "Techron Gasohol95" in location["fuelsName"]
                    or "Techron Gold95" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.OCTANE_92, item, "Regular 92 with Techron" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.OCTANE_91,
                    item,
                    "Unleaded 91" in location["fuelsName"]
                    or "Silver with Techron" in location["fuelsName"]
                    or "Techron Gasohol91" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.E10, item, "Unleaded E10" in location["fuelsName"], False)
                apply_yes_no(Fuel.E20, item, "Gasohol E20" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.LPG, item, "LPG" in location["fuelsName"] or "AutoGas" in location["fuelsName"], False
                )
                apply_yes_no(
                    Fuel.DIESEL,
                    item,
                    "Diesel" in location["fuelsName"]
                    or "Premium Diesel" in location["fuelsName"]
                    or "Diesel Euro5 B10" in location["fuelsName"]
                    or "Power Diesel Euro5 B7" in location["fuelsName"]
                    or "Power Diesel with Techron D Euro 5" in location["fuelsName"]
                    or "Diesel with Techron D" in location["fuelsName"]
                    or "Techron D Diesel B7" in location["fuelsName"]
                    or "Techron D Diesel B10" in location["fuelsName"]
                    or "Techron D Diesel B20" in location["fuelsName"]
                    or "Techron D Power Diesel" in location["fuelsName"],
                    False,
                )
                apply_yes_no(
                    Fuel.ENGINE_OIL,
                    item,
                    "Havoline Engine Oil" in location["fuelsName"] or "Delo Diesel Engine Oil" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.ADBLUE, item, "Bulk AdBlue" in location["fuelsName"], False)
                apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in location["fuelsName"], False)

            if "/au/" in response.url:
                # Other countries use different wording that is not handled here.
                item["opening_hours"] = self.parse_au_opening_hours(location.get("operatingHours"))

            apply_category(Categories.FUEL_STATION, item)

            yield item
