import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class DenizbankTRSpider(scrapy.Spider):
    name = "denizbank_tr"
    allowed_domains = ["denizbank.com"]
    item_attributes = {"brand": "Denizbank", "brand_wikidata": "Q1115064"}
    start_urls = [
        "https://www.denizbank.com/api/branch-atm?isAtmSearch=true&isBranchSearch=true&isVisuallyImparied=false&isOrthopedicalHandicapped=false&isCurrencySupport=false&keyword=&latitude=&longitude=&cityCode=&townCode=",
    ]

    def parse(self, response):
        data = response.json()
        for poi in data:
            item = DictParser.parse(poi)
            # TODO: map "is-visually-imparied", "is-orthopedical-handicapped", "is-exchange-support" to OSM tags if possible
            item["ref"] = poi.get("code")
            item["phone"] = poi.get("phone").strip() if poi.get("phone") else None
            if poi["record-type"] == "atm":
                apply_category(Categories.ATM, item)
            if poi["record-type"] == "branch":
                apply_category(Categories.BANK, item)
            yield item
