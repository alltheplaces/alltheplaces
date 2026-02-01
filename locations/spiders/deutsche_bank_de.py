from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class DeutscheBankDESpider(Spider):
    name = "deutsche_bank_de"
    item_attributes = {"brand": "Deutsche Bank", "brand_wikidata": "Q66048"}
    SPARDA_BANK = {"brand": "Sparda-Bank", "brand_wikidata": "Q2307136"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "CONCURRENT_REQUEST": 1, "DOWNLOAD_DELAY": 3}

    async def start(self) -> AsyncIterator[JsonRequest]:
        base_url = "https://www.deutsche-bank.de/cip/rest/api/url/pfb/content/gdata/Presentation/DbFinder/Home/IndexJson?label={type}&searchTerm={searchBy}&country=D"

        for city in city_locations("DE", 15000):
            yield JsonRequest(base_url.format(searchBy=city["name"], type="BRANCH"))
            yield JsonRequest(f"{base_url}&branches=PBCxATM%7CSPADxxBW".format(searchBy=city["name"], type="ATM"))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if "errorpage" in response.url:
            return

        for location in response.json()["Items"]:
            location["location"] = location.pop("LatLng")
            location["Address"] = location["Item"]["BasicData"].pop("Address")
            location["Address"]["street_address"] = location["Address"]["StreetWithHouseNo"]
            location["Address"]["state"] = location["Address"]["District"]
            location.update(location["Item"]["BasicData"]["Contact"])

            item = DictParser.parse(location)

            item["housenumber"] = item["street"] = None

            item["website"] = (
                f'https://www.deutsche-bank.de/cip/rest/api/url/filialfinder/Home/Details?id={location["ID"]}'
            )

            item["country"] = "DE"

            item["extras"]["type"] = location_type = location["CurrentBranch"]["BranchType"]

            if location_type in ["PBCxFIN", "PBCxINV", "PBCxPRIBC", "PBCxSEL"]:
                apply_category(Categories.BANK, item)
                oh_item_key = "Item1"

                if self_services := location.get("SelfServices"):
                    has_cash_out = "Bargeldauszahlung" in self_services
                    has_cash_in = "Bargeldeinzahlung" in self_services
                    apply_yes_no(Extras.ATM, item, has_cash_out or has_cash_in)
                    apply_yes_no(Extras.CASH_IN, item, has_cash_in, False)
                    apply_yes_no(Extras.CASH_OUT, item, has_cash_out, False)

            elif location_type in ["PBCxATM", "SPADxxBW"]:
                apply_category(Categories.ATM, item)
                oh_item_key = "Item2"

                if location_type == "SPADxxBW":
                    item.update(self.SPARDA_BANK)

            else:
                continue

            item["opening_hours"] = OpeningHours()
            for openingHour in location["OpeningHours"]:
                if rule := openingHour.get(oh_item_key):
                    if day := sanitise_day(rule["Day"], DAYS_DE):
                        for period in ["Morning", "Afternoon"]:
                            if not rule.get(period):
                                continue
                            item["opening_hours"].add_range(day, rule[period]["From"], rule[period]["Until"])

            yield item
