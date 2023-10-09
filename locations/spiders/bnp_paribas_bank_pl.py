import scrapy
from chompjs import chompjs

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

BRANDS = {
    "BNP Paribas Bank Polska": ("BNP Paribas Bank Polska", "Q20744004"),
    "Euronet": ("Euronet", "Q5412010"),
    "Planet Cash": ("Planet Cash", "Q117744569"),
}


class BNPParibasBankPLSpider(scrapy.Spider):
    name = "bnp_paribas_bank_pl"
    start_urls = ["https://www.bnpparibas.pl/_js_places/time20230712142358/places.js"]

    def parse(self, response, **kwargs):
        details = chompjs.parse_js_object(response.text)

        for poi in details.get("department_retail_business").values():
            branch = poi.get("basicParameters")
            branch["street_address"] = branch.pop("street")
            item = DictParser.parse(branch)
            item["ref"] = branch["branch_id"]
            item["brand"], item["brand_wikidata"] = BRANDS.get("BNP Paribas Bank Polska")

            oh = OpeningHours()
            for day, times in branch["opening_hours"].items():
                start_time, end_time = times.split("-")
                oh.add_range(DAYS[int(day) - 2], start_time, end_time)

            item["opening_hours"] = oh.as_opening_hours()
            apply_category(Categories.BANK, item)
            yield item

        for key, poi in details.get("atm").items():
            branch = poi.get("basicParameters")
            branch["street_address"] = branch.pop("street")
            item = DictParser.parse(branch)
            item["ref"] = key
            item["opening_hours"] = "24/7"

            attributes = poi.get("additionalAttributes", [])

            brand_key = "BNP Paribas Bank Polska"  # Default brand

            if "atm-planet_cash" in attributes:
                brand_key = "Planet Cash"
            elif "atm-euronet" in attributes:
                brand_key = "Euronet"

            item["brand"], item["brand_wikidata"] = BRANDS.get(brand_key)
            apply_yes_no(Extras.CASH_IN, item, "atm_in" in attributes)
            apply_yes_no(Extras.CASH_OUT, item, "atm-cash_out" in attributes)
            apply_category(Categories.ATM, item)
            yield item
