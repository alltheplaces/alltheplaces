import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import FIREFOX_LATEST


class SamsClubSpider(SitemapSpider):
    name = "sams_club"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}
    allowed_domains = ["www.samsclub.com"]
    sitemap_urls = ["https://www.samsclub.com/sitemap_locators.xml"]
    user_agent = FIREFOX_LATEST

    depts = {
        "GAS": ("/local/fuel-center/", Categories.FUEL_STATION),
        # "PHARMACY": ("/local/pharmacy/", Categories.PHARMACY),
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        [script] = filter(
            lambda script: "clubDetails" in script,
            response.xpath('//script[@type="application/json"]/text()').extract(),
        )
        data = json.loads(script)["clubDetails"]

        if data["clubType"] in ["HOME_OFFICE", "TEST"]:
            return
        elif data["clubType"] == "REGULAR":
            pass
        else:
            self.logger.error("Unexpected club: {}".format(data["clubType"]))

        item = DictParser.parse(data)
        item["name"] = None
        item["website"] = response.url
        item["opening_hours"] = self.parse_opening_hours(data["operationalHours"])

        for service in data["services"]:
            if service["name"] not in self.depts:
                continue
            dept = item.deepcopy()
            dept["ref"] = "{}-{}".format(item["ref"], service["name"])
            dept["website"] = item["website"].replace("/club/", self.depts[service["name"]][0])
            dept["opening_hours"] = self.parse_opening_hours(service["operationalHours"])

            if phone := service.get("phone"):
                dept["phone"] = phone

            apply_category(self.depts[service["name"]][1], dept)

            yield dept
        # TODO: gasPrices

        apply_category(Categories.SHOP_WHOLESALE, item)
        yield item

    def parse_opening_hours(self, operational_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, interval in operational_hours.items():
            oh.add_range(day[:2], interval["startHrs"], interval["endHrs"])
        return oh
