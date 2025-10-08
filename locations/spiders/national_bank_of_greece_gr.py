from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class NationalBankOfGreeceGRSpider(Spider):
    name = "national_bank_of_greece_gr"
    item_attributes = {"brand_wikidata": "Q1816028", "country": "GR"}

    def start_requests(self):
        url = "https://www.nbg.gr/sitecore/api/layout/render/jss?item=%2Fidiwtes%2Fkatastimata-atm&sc_lang=el&sc_apikey=%7B029DC798-60FC-4E8D-94BF-6A8AF0AAE4DA%7D"
        yield Request(url=url)

    def parse(self, response):
        data = response.json()

        results = (
            data.get("sitecore", {})
            .get("route", {})
            .get("placeholders", {})
            .get("jss-main", [{}])[0]
            .get("fields", {})
            .get("result", {})
        )

        # Go through Once to get all the Branches. By checking what Feature codes are present
        for poi in results.get("BranchMapList", []):
            if poi.get("IsBranch"):
                item = self.parse_poi(poi)
                apply_category(Categories.BANK, item)
                item["ref"] = poi.get("BranchId")
                item["branch"] = item.pop("name")
                item["phone"] = poi.get("PhoneOne")

                yield item

            else:
                item = self.parse_poi(poi)
                apply_category(Categories.ATM, item)
                item["ref"] = poi.get("Code")

                yield item

    def parse_poi(self, poi):
        item = DictParser.parse(poi)
        item["city"] = poi.get("Location")
        return item
