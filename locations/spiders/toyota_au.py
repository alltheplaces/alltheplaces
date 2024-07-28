from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ToyotaAUSpider(Spider):
    name = "toyota_au"
    item_attributes = {"brand": "Toyota", "brand_wikidata": "Q53268"}
    allowed_domains = ["www.toyota.com.au"]
    start_urls = [
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/ACT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NSW?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/QLD?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/SA?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/TAS?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/VIC?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/WA?dealerOptIn=false",
    ]
    requires_proxy = "AU"

    def parse(self, response):
        for location in response.json()["results"]:
            for location_type in ["sales", "service", "parts"]:
                if not location[location_type]:
                    continue
                item = DictParser.parse(location)
                item["ref"] = location["branchCode"] + "_" + location_type
                item["lat"] = location["refY"]
                item["lon"] = location["refX"]
                item["state"] = location["state"]
                item["street_address"] = location.pop("addr_full", None)
                if location_type == "sales":
                    apply_category(Categories.SHOP_CAR, item)
                elif location_type == "service":
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                elif location_type == "parts":
                    apply_category(Categories.SHOP_CAR_PARTS, item)
                yield item
