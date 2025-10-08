from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_EN, DAYS_FR, OpeningHours, sanitise_day

PHARMAPRIX = {"name": "Pharmaprix", "brand": "Pharmaprix", "brand_wikidata": "Q1820137"}
SHOPPERS_DRUG_MART = {"name": "Shoppers Drug Mart", "brand": "Shoppers Drug Mart", "brand_wikidata": "Q1820137"}
SHOPPERS_SIMPLY_PHARMACY = {
    "name": "Shoppers Simply Pharmacy",
    "brand": "Shoppers Drug Mart",
    "brand_wikidata": "Q1820137",
}


class ShoppersDrugMartCASpider(Spider):
    name = "shoppers_drug_mart_ca"

    def start_requests(self) -> Iterable[Request]:
        for store_type in ["pharmaprix", "shoppersdrugmart"]:
            for city in city_locations("CA", 90000):
                yield JsonRequest(
                    url=f"https://api.shoppersdrugmart.ca/beauty/v2/{store_type}/store-locator/search?lang=en",
                    headers={"x-apikey": "r3kEMAxRsQQtyjXiIJOTFNN75vcsJFxH"},
                    data={"radius": 5000.166034400522, "longitude": city["longitude"], "latitude": city["latitude"]},
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["layout"]["sections"]["mainContentCollection"]["components"][0]["data"]:
            item = DictParser.parse(store)
            item["ref"] = store["viewStoreDetailsCTA"].rsplit("/", 1)[1]
            item["website"] = store["viewStoreDetailsCTA"]

            if (
                store["canadaPostOfficeCTA"]
                and store["canadaPostOfficeCTA"]
                != "https://www.canadapost-postescanada.ca/cpc/en/tools/find-a-post-office.page?outletId=&detail=true"
            ):
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:website"] = store["canadaPostOfficeCTA"]

            item["branch"] = item.pop("name")
            if store["bannerName"] == "PHARMAPRIX":
                item.update(PHARMAPRIX)
                apply_category(Categories.PHARMACY, item)
            elif store["bannerName"] == "SHOPPERS DRUG MART":
                item.update(SHOPPERS_DRUG_MART)
                apply_category(Categories.PHARMACY, item)
            elif store["bannerName"] == "SHOPPERS SIMPLY PHARMACY":
                item.update(SHOPPERS_SIMPLY_PHARMACY)
                apply_category(Categories.PHARMACY, item)
            else:
                continue
            item["branch"] = item["branch"].removeprefix(item["name"]).strip()

            item["opening_hours"] = self.parse_opening_hours(store["storeHours"])

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = sanitise_day(rule["nameOfDay"], DAYS_FR | DAYS_EN)
            if rule["timeRange"] == "Closed":
                oh.set_closed(day)
            elif rule["timeRange"] == "24 hours":
                oh.add_range(day, "00:00", "24:00")
            else:
                oh.add_range(
                    day, *rule["timeRange"].replace("Midnight", "12:00 AM").split(" - "), time_format="%I:%M %p"
                )

        return oh
