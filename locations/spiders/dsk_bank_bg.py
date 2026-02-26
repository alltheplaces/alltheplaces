import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class DskBankBGSpider(scrapy.Spider):
    name = "dsk_bank_bg"
    item_attributes = {"brand": "Банка ДСК", "brand_wikidata": "Q5206146"}
    allowed_domains = ["https://www.dskbank.bg/", "https://dskbank.bg/"]
    start_urls = ["https://dskbank.bg/GetOfficesData?cultureName=bg"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)
            item["ref"] = data["office_id"]
            item["name"] = data["office_name"]
            item["street_address"] = data["office_address"]
            item["lat"] = data["office_latitude"]
            item["lon"] = data["office_longitude"]
            if (data["office_type"] == ["Branch", "Atm"]) or (data["office_type"] == ["Branch"]):
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, True if "Atm" in data["office_type"] else False)
            elif data["office_type"] == ["Atm"]:
                apply_category(Categories.ATM, item)
            yield item
