import json

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class VakifBankTRSpider(scrapy.Spider):
    name = "vakifbank_tr"
    item_attributes = {"brand": "Vakıfbank", "brand_wikidata": "Q1148521"}
    allowed_domains = ["vakifbank.com.tr"]

    def start_requests(self):
        url = "https://maps.vakifbank.com.tr/API/api/v1/Search/GetAllBranchAndAtmWithFiltersObj"
        payload = {
            "CountryId": 0,
            "WhichOne": 1,
            "BranchNameOrCode": "",
            "CityId": -1,
            "TownId": -1,
            "NeighborhoodId": -1,
            "Options": [],
        }
        yield JsonRequest(url=url, method="POST", body=json.dumps(payload), callback=self.parse)
        payload['WhichOne'] = 2
        yield JsonRequest(url=url, method="POST", body=json.dumps(payload), callback=self.parse)

    def parse(self, response, **kwargs):
        data = response.json()
        for poi in data.get("ReturnObjectList"):
            item = Feature()
            # TODO: attributes "Branch/ATM for Physically Disabled", "Branch/ATM for Visualy Disabled" and "Foreign Withdrawal ATM"
            item["ref"] = poi[7]
            item["lat"] = poi[0]
            item["lon"] = poi[1]
            item["name"] = poi[2]
            item["addr_full"] = poi[6]
            item["phone"] = poi[4]
            if poi[8] == "ATM":
                apply_category(Categories.ATM, item)
            if poi[8] == "SUBE":
                apply_category(Categories.BANK, item)
            yield item
