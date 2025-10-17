from json.decoder import JSONDecodeError

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BankOfBarodaINSpider(scrapy.Spider):
    name = "bank_of_baroda_in"
    item_attributes = {"brand": "Bank of Baroda", "brand_wikidata": "Q2003797"}
    start_urls = [
        "https://www.bankofbaroda.in/js/bob/countrywebsites/India/atmMaster.js",
        "https://www.bankofbaroda.in/js/bob/countrywebsites/India/branchesMaster.js",
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response):
        try:
            stores = chompjs.parse_js_object(response.text, json_params={"strict": False})
        except JSONDecodeError:
            stores = chompjs.parse_js_object(response.text.replace("\\", ""), json_params={"strict": False})
        for store in stores:
            store["postal-code"] = store.pop("pincode", None)
            if not store["postal-code"]:
                store["postal-code"] = store.pop("PIN_CODE", None)
            store["postal-code"] = str(store["postal-code"])
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            if "branch_id" in store:
                item["ref"] = store["branch_id"]
                apply_category(Categories.BANK, item)
            elif "ATMID" in store:
                item["ref"] = store["ATMID"]
                apply_category(Categories.ATM, item)
            yield item
