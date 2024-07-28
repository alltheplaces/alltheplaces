import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class DskBankBGSpider(scrapy.Spider):
    name = "dsk_bank_bg"
    item_attributes = {"brand": "Банка ДСК", "brand_wikidata": "Q5206146"}
    allowed_domains = ["https://www.dskbank.bg/"]
    start_urls = ["https://dskbank.bg/контакти/клонова-мрежа/GetOffices/"]

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)

            if "Branch" in data["BranchType"]:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)

            if data["Phone"]:
                item["phone"] = data.get("Phone").split(";", 1)[0]

            item["opening_hours"] = OpeningHours()

            if data["OpenHours"]:
                item["opening_hours"].add_ranges_from_string(data["OpenHours"], days=DAYS_BG)
            yield item
