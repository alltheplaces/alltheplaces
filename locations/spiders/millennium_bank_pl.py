import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MillenniumBankPLSpider(Spider):
    name = "millennium_bank_pl"
    item_attributes = {"brand": "Bank Millennium", "brand_wikidata": "Q4855947"}
    start_urls = ["https://www.bankmillennium.pl/en/about-the-bank/branches-and-atms"]

    def parse(self, response, **kwargs):
        map_config = json.loads(response.xpath("//wc-facilities-map/@config").get())
        yield JsonRequest(url=response.urljoin(map_config["branchesUrl"]), callback=self.parse_branches)
        yield JsonRequest(url=response.urljoin(map_config["atmsUrl"]), callback=self.parse_atms)

    def parse_branches(self, response, **kwargs):
        for branch in response.json():
            item = DictParser.parse(branch)
            item["lat"] = branch["branchLat"]
            item["lon"] = branch["branchLng"]
            item["ref"] = branch["branch"]
            item["street_address"] = branch["address_Street"]
            item["city"] = branch["address_City"]
            item["opening_hours"] = self.parse_branch_opening_hours(branch)
            apply_yes_no(Extras.WHEELCHAIR, item, branch["disabledPersonsFriendly_Movement"] == "1")
            apply_category(Categories.BANK, item)
            yield item

    def parse_branch_opening_hours(self, data):
        opening_hours = OpeningHours()
        for key in data.keys():
            if key.startswith("openHours_"):
                day = key.removeprefix("openHours_")
                opening_hours.add_ranges_from_string(f"{day} {data[key]}")
        return opening_hours

    def parse_atms(self, response, **kwargs):
        for atm in response.json():
            item = DictParser.parse(atm)
            item["ref"] = atm["name"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(atm["officeHours"])
            apply_category(Categories.ATM, item)
            yield item
