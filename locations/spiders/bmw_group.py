import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

# POI Types mapping found in https://dlo.api.bmw/main.js
"""
{
  "newCars": [{ "type": "distributionBranches", "key": "F" }],
  "usedCars": [{ "type": "distributionBranches", "key": "G" }],
  "repairServices": [{ "type": "distributionBranches", "key": "T" }],
  "mCertified": [{ "type": "businessTypes", "key": "MC" }],
  "classicCertified": [{ "type": "businessTypes", "key": "CC" }],
  "eRetail": [{ "type": "requestServices", "key": "SON" }],
  "highVoltageServices": [{ "type": "services", "key": "HV" }],
  "carbonServices": [{ "type": "services", "key": "CR" }],
  "bodyShop": [{ "type": "requestServices", "key": "CBS" }],
  "paintShop": [{ "type": "requestServices", "key": "CPS" }],
  "onlineBooking": [{ "type": "testDriveBooking", "key": "TDB_OB" }],
  "sendRequest": [{ "type": "testDriveBooking", "key": "TDB_SR" }],
  "bmwEmployeeDelivery": [{ "type": "businessTypes", "key": "GE" }]
}
"""


class BmwGroupSpider(scrapy.Spider):
    name = "bmw_group"
    available_countries = [
        "LU",
        "JP",
        "FO",
        "DK",
        "AR",
        "CA",
        "AE",
        "DZ",
        "RO",
        "AU",
        "KY",
        "SK",
        "IQ",
        "TM",
        "VN",
        "DE",
        "SE",
        "SR",
        "HU",
        "PT",
        "AG",
        "BE",
        "BD",
        "LK",
        "MD",
        "QA",
        "RS",
        "GH",
        "ID",
        "RE",
        "SV",
        "BG",
        "UA",
        "MQ",
        "KH",
        "LY",
        "IE",
        "NZ",
        "JO",
        "BL",
        "CW",
        "CZ",
        "LA",
        "LB",
        "MY",
        "GT",
        "NL",
        "PS",
        "ZM",
        "MO",
        "CH",
        "MG",
        "SG",
        "GR",
        "TW",
        "US",
        "AW",
        "BR",
        "CL",
        "EC",
        "IN",
        "BH",
        "SI",
        "BB",
        "PL",
        "DO",
        "MX",
        "SA",
        "TN",
        "FR",
        "JM",
        "RW",
        "BJ",
        "LT",
        "TR",
        "LC",
        "PH",
        "NP",
        "PF",
        "MM",
        "AT",
        "PA",
        "BM",
        "RU",
        "AM",
        "AL",
        "BA",
        "NC",
        "KZ",
        "MA",
        "PK",
        "UY",
        "BN",
        "BS",
        "TH",
        "GP",
        "KW",
        "AZ",
        "IL",
        "ME",
        "HN",
        "KR",
        "MU",
        "NO",
        "OM",
        "NG",
        "IS",
        "TT",
        "GF",
        "ZA",
        "BO",
        "GB",
        "GE",
        "KG",
        "CO",
        "MT",
        "HR",
        "CY",
        "HT",
        "SC",
        "EE",
        "GU",
        "PE",
        "KE",
        "ES",
        "CR",
        "PY",
        "FI",
        "IT",
        "MK",
        "BY",
        "LV",
    ]

    BMW_MOTORBIKE = "BMW_MOTORBIKE"
    BRAND_MAPPING = {
        "BMW": {"brand": "BMW", "brand_wikidata": "Q26678"},
        "BMW_I": {"brand": "BMW i", "brand_wikidata": "Q796784"},
        "ROLLS_ROYCE": {"brand": "Rolls-Royce", "brand_wikidata": "Q243278"},
        "BMW_M": {"brand": "BMW M", "brand_wikidata": "Q173339"},
        "MINI": {"brand": "Mini", "brand_wikidata": "Q116232"},
        BMW_MOTORBIKE: {"brand": "BMW Motorrad", "brand_wikidata": "Q249173"},
    }

    def start_requests(self):
        for country in self.available_countries:
            url = f"https://c2b-services.bmw.com/c2b-localsearch/services/api/v4/clients/BMWSTAGE2_DLO/-/pois?cached=off&language=en&lat=0&lng=0&maxResults=10000&unit=km&showAll=true&country={country}"
            yield scrapy.Request(
                url=url, callback=self.parse, headers={"Accept": "application/json", "Content-Type": "application/json"}
            )

    def parse(self, response):
        if response.status == 204:
            self.logger.info(f"No content found in {response.url}")
        else:
            response = response.json().get("data").get("pois")
            for data in response:
                data["street_address"] = data.pop("street")

                item = DictParser.parse(data)
                item["ref"] = f"{data.get('key', '')}-{data.get('category','')}"
                item["phone"] = data.get("attributes", {}).get("phone")
                item["email"] = data.get("attributes", {}).get("mail")
                item["website"] = data.get("attributes", {}).get("homepage")

                if match := self.BRAND_MAPPING.get(data.get("category")):
                    item.update(match)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/brand/fail/{data.get('category')}")
                    self.logger.error(f"Unknown brand: {data.get('category')}, {item['ref']}")

                self.map_category(item, data)

                yield item

    def map_category(self, item: Feature, poi: dict):
        distribution_branches = poi.get("distributionBranches", [])

        if poi.get("category") == self.BMW_MOTORBIKE:
            if "F" or "G" in distribution_branches:
                apply_category(Categories.SHOP_MOTORCYCLE, item)
                apply_yes_no(Extras.USED_MOTORCYCLE_SALES, item, "G" in distribution_branches)
                apply_yes_no(Extras.MOTORCYCLE_REPAIR, item, "T" in distribution_branches)
            elif "T" in distribution_branches:
                apply_category(Categories.SHOP_MOTORCYCLE_REPAIR, item)
            else:
                for branch in distribution_branches:
                    self.crawler.stats.inc_value(f"atp/{self.name}/distribution_branch/fail/{branch}")
                    self.logger.error(f"Unknown distribution branch: {branch}, {item['ref']}")
            return

        if "F" or "G" in distribution_branches:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.USED_CAR_SALES, item, "G" in distribution_branches)
            apply_yes_no(Extras.CAR_REPAIR, item, "T" in distribution_branches)
        elif "T" in distribution_branches:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            for branch in distribution_branches:
                self.crawler.stats.inc_value(f"atp/{self.name}/distribution_branch/fail/{branch}")
                self.logger.error(f"Unknown distribution branch: {branch}, {item['ref']}")
