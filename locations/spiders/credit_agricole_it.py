import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CreditAgricoleITSpider(scrapy.Spider):
    name = "credit_agricole_it"
    item_attributes = {"brand": "Crédit Agricole", "brand_wikidata": "Q2938832"}
    start_urls = ["https://www.credit-agricole.it/api/districts/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        district_id = [district["value"] for district in response.json()]
        for dist in district_id:
            url_template = "https://www.credit-agricole.it/api/districts/{}/offices"
            yield scrapy.Request(url=url_template.format(dist), callback=self.parse_poi)

    def parse_poi(self, response):
        for poi in response.json():
            item = DictParser.parse(poi)
            item["branch"] = item.pop("name")
            item["lon"], item["lat"] = poi.get("coordinates")
            if poi["bank_counter"]:
                apply_category(Categories.BANK, item)
            elif not poi["bank_counter"]:
                apply_category(Categories.ATM, item)
            yield item
