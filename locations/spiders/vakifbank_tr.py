import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class VakifbankTRSpider(scrapy.Spider):
    name = "vakifbank_tr"
    item_attributes = {"brand": "Vakıfbank", "brand_wikidata": "Q1148521"}
    allowed_domains = ["vakifbank.com.tr"]
    requires_proxy = "TR"
    no_refs = True

    def start_requests(self):
        url = "https://maps.vakifbank.com.tr/API/api/v1/Search/GetAllBranchAndAtmWithFiltersObj"
        payload = {
            "CountryId": 0,
            "WhichOne": 1,  # Branches
            "BranchNameOrCode": "",
            "CityId": -1,
            "TownId": -1,
            "NeighborhoodId": -1,
            "Options": [],
        }
        yield JsonRequest(url=url, data=payload, callback=self.parse)
        payload["WhichOne"] = 2  # ATMs
        yield JsonRequest(url=url, data=payload, callback=self.parse)

    def parse(self, response, **kwargs):
        data = response.json()
        for poi in data.get("ReturnObjectList"):
            item = Feature()
            item["ref"] = poi[7]
            item["lat"] = poi[0]
            item["lon"] = poi[1]
            item["name"] = poi[2]
            item["addr_full"] = poi[6]
            item["phone"] = poi[4]
            if poi[8] == "ATM":
                apply_category(Categories.ATM, item)
            if poi[8] == "SUBE" or poi[8] == "B_SUBE":
                apply_category(Categories.BANK, item)
            yield item
