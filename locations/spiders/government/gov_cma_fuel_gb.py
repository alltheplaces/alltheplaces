from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class GovCmaFuelGBSpider(Spider):
    name = "gov_cma_fuel_gb"
    dataset_attributes = {
        "license": "Open Government Licence v3.0",
        "license:website": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "license:wikidata": "Q99891702",
        "attribution": "required",
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0.",
    }
    start_urls = ["https://www.gov.uk/guidance/access-fuel-price-data"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # Asda, Shell!
        "USER_AGENT": BROWSER_DEFAULT,  # TESCO!
    }

    brand_map = {
        "asda": {"brand": "Asda", "brand_wikidata": "Q297410"},
        "asda express": {"brand": "Asda Express", "brand_wikidata": "Q114826023"},
        "bp": {"brand": "BP", "brand_wikidata": "Q152057"},
        "coop": None,
        "essar": {"brand": "Essar", "brand_wikidata": "Q5399372"},
        "esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "jet": {"brand": "JET", "brand_wikidata": "Q568940"},
        "morrisons": {"brand": "Morrisons", "brand_wikidata": "Q922344"},
        "murco": {"brand": "Murco", "brand_wikidata": "Q16998281"},
        "sainsbury's": {"brand": "Sainsbury's", "brand_wikidata": "Q152096"},
        "shell": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "tesco": {"brand": "Tesco", "brand_wikidata": "Q487494"},
        "texaco": {"brand": "Texaco", "brand_wikidata": "Q775060"},
        "valero": {"brand": "Valero", "brand_wikidata": "Q1283291"},
    }

    fuel_map = {
        "B7": "diesel",
        "E10": "e10",
        "E5": "e5",
        # "SDV": "ethanol", # TODO: ?
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath("//table/tbody/tr/td[2]/text()").getall():
            yield JsonRequest(url, self.parse_locations)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stations"]:
            item = Feature()
            item["ref"] = location["site_id"]
            item["addr_full"] = location["address"]
            item["postcode"] = location.get("postcode")
            item["lat"] = location["location"]["latitude"]
            item["lon"] = location["location"]["longitude"]

            if brand := self.brand_map.get((location.get("brand") or "").lower().strip()):
                item.update(brand)
                item["name"] = item.get("brand")
            else:
                self.crawler.stats.inc_value("atp/gov_cma_fuel_gb/upmapped_brand/{}".format(location["brand"]))

            for fuel, price in location["prices"].items():
                if not price:
                    continue

                if price < 10:
                    # BP, sgnretail, Tesco!
                    price *= 100

                tag = self.fuel_map.get(fuel, fuel)
                item["extras"]["charge:{}".format(tag)] = "{} GBP/1 litre".format(round(price / 100, 2))
                apply_yes_no("fuel:{}".format(tag), item, True)

            apply_category(Categories.FUEL_STATION, item)

            yield item
