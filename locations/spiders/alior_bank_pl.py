import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class AliorBankPLSpider(Spider):
    name = "alior_bank_pl"
    item_attributes = {"brand": "Alior Bank", "brand_wikidata": "Q9148395"}
    start_urls = ["https://www.aliorbank.pl/en/branches.html"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath("//script[@id='branch']/text()").get())
        services = {
            service.xpath("./@for").get().removeprefix("p[").strip("]"): service.xpath("./text()").get("").strip()
            for service in response.xpath('//label[contains(@for, "p[")]')
        }
        for city, branches in data.items():
            for branch in branches:
                item = Feature()
                item["postcode"] = branch["pc"]
                item["city"] = city
                item["street_address"] = branch["s"]
                item["name"] = branch["n"]
                item["lat"] = branch["lt"]
                item["lon"] = branch["lg"]
                item["ref"] = branch["o"]
                self.parse_opening_hours(item, branch["h"])
                apply_category(Categories.BANK, item)

                if branch_service_ids := branch.get("p"):
                    branch_services = [services.get(service_id) for service_id in branch_service_ids]
                    apply_yes_no(Extras.ATM, item, "ATM" in branch_services)

                yield item

    # based on _renderOpenHours in JavaScript
    def parse_opening_hours(self, item: Feature, openings: list) -> None:
        item["opening_hours"] = OpeningHours()
        if openings[-1]["d"] == "7":
            item["opening_hours"].add_ranges_from_string(f"Mo-Fr {openings[-1]['h']}")
            for opening in openings[:-1]:
                item["opening_hours"].add_ranges_from_string(f"{DAYS[int(opening['d'])]} {opening['h']}")
        else:
            for opening in openings:
                item["opening_hours"].add_ranges_from_string(f"{DAYS[int(opening['d'])]} {opening['h']}")
