import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CalvinKleinSpider(scrapy.Spider):
    name = "calvin_klein"
    item_attributes = {"brand": "Calvin Klein", "brand_wikidata": "Q1068628"}

    def start_requests(self):
        for region in [
            "CalvinKleinAT",
            "CalvinKleinBE",
            "CalvinKleinBG",
            "CalvinKleinCH",
            "CalvinKleinCZ",
            "CalvinKleinDE",
            "CalvinKleinDK",
            "CalvinKleinEE",
            "CalvinKleinES",
            "CalvinKleinFI",
            "CalvinKleinFR",
            "CalvinKleinHR",
            "CalvinKleinHU",
            "CalvinKleinIE",
            "CalvinKleinIT",
            "CalvinKleinLT",
            "CalvinKleinLU",
            "CalvinKleinLV",
            "CalvinKleinNL",
            "CalvinKleinPL",
            "CalvinKleinPT",
            "CalvinKleinRO",
            "CalvinKleinRU",
            "CalvinKleinSE",
            "CalvinKleinSI",
            "CalvinKleinSK",
            "CalvinKleinUK",  # GB
        ]:
            yield JsonRequest(
                url="https://live.ck.prd.b2c-api.eu.pvh.cloud/physical-stores?page[limit]=100",
                headers={"accept-store": region},
                dont_filter=True,  # by default scrapy dedups requests but doesn't account for headers
            )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            location["address"]["street_address"] = clean_address(location["address"].pop("addressLines"))
            item = DictParser.parse(location)

            oh = OpeningHours()
            for rule in location["openingTimes"]:
                if rule["status"] == "OPEN":
                    for period in rule["times"]:
                        oh.add_range(rule["day"], period["from"], period["to"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item

        if next_page := response.json().get("links", {}).get("next"):
            yield response.follow(url=next_page, headers={"accept-store": response.request.headers["accept-store"]})
