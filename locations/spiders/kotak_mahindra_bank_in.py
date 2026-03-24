import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class KotakMahindraBankINSpider(scrapy.Spider):
    name = "kotak_mahindra_bank_in"
    item_attributes = {"brand": "Kotak Mahindra Bank", "brand_wikidata": "Q2040404"}
    handle_httpstatus_list = [502]
    start_urls = [
        "https://www.kotak.com/content/kotakcl/en/reach-us/_jcr_content/mid_par/maps.map.reachus.MA==.MA==.MA==.dXNlclNlYXJjaA==.0.bnVsbA==.json"
    ]

    def parse(self, response):
        for data in response.json()["BranchList"]:
            item = Feature()
            item["name"] = data["branchOrATMName"]
            item["ref"] = data["identityValue"]
            item["addr_full"] = data["addressValue"]
            item["lon"] = data["longitudeValue"]
            item["lat"] = data["latitudeValue"]
            item["postcode"] = str(data["pincodeNumber"])
            item["city"] = data["cityName"]
            item["state"] = data["stateName"]
            if "ATM" in data["branchOrATMName"]:
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
            yield item
