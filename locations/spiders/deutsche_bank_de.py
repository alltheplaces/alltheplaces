from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class DeutscheBankDESpider(Spider):
    name = "deutsche_bank_de"
    item_attributes = {"brand": "Deutsche Bank", "brand_wikidata": "Q66048"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        base_url = "https://www.deutsche-bank.de/cip/rest/api/url/pfb/content/gdata/Presentation/DbFinder/Home/IndexJson?label={type}&searchTerm={searchBy}&country=D"

        for city in city_locations("DE", 25000):
            yield JsonRequest(base_url.format(searchBy=city["name"], type="BRANCH"))

    def parse(self, response):
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

            item["country"] = ""

            item["extras"]["type"] = location["CurrentBranch"]["BranchType"]

            if location["CurrentBranch"]["BranchType"] in ["PBCxFIN", "PBCxINV", "PBCxPRIBC", "PBCxSEL"]:
                apply_category(Categories.BANK, item)
                oh_item_key = "Item1"
            elif location["CurrentBranch"]["BranchType"] in ["CGGA" "CGSH" "EHSB" "PBCxATM"]:
                apply_category(Categories.ATM, item)
                oh_item_key = "Item2"
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
