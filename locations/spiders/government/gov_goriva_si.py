from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser

# https://www.gov.si/novice/2020-09-28-spletna-aplikacija-goriva-si/


class GovGorivaSISpider(Spider):
    name = "gov_goriva_si"
    brands = {
        1: {"brand": "Petrol", "brand_wikidata": "Q174824"},
        3: {"brand": "MAXEN"},
        4: {"brand": "MOL", "brand_wikidata": "Q549181"},
        5: {"name": "Shell", "brand": "Shell", "brand_wikidata": "Q110716465"},
    }
    fuels = {
        "95": "octane_95",
        "dizel": "diesel",
        "98": "octane_98",
        "100": "octane_100",
        "dizel-premium": None,
        "avtoplin-lpg": "lpg",
        "KOEL": None,
        "hvo": "biodiesel",
        "cng": "cng",
        "lng": "lng",
    }

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://goriva.si/api/v1/search/?format=json")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["results"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["ref"] = location["pk"]

            for fuel, price in location["prices"].items():
                if tag := self.fuels.get(fuel):
                    if not price:
                        continue
                    item["extras"]["charge:{}".format(tag)] = "{} EUR/1 litre".format(price)
                    apply_yes_no("fuel:{}".format(tag), item, True)
                else:
                    self.crawler.stats.inc_value("{}/unmapped_fuel/{}".format(self.name, fuel))

            if b := self.brands.get(location["franchise"]):
                item.update(b)
            else:
                self.crawler.stats.inc_value("{}/unmapped_franchise/{}".format(self.name, location["franchise"]))

            apply_category(Categories.FUEL_STATION, item)

            yield item

        if next_url := response.json()["next"]:
            yield JsonRequest(url=next_url)
