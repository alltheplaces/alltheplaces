from urllib.parse import urljoin, urlparse

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


class BnpParibasBankPLSpider(scrapy.Spider):
    name = "bnp_paribas_bank_pl"
    start_urls = ["https://www.bnpparibas.pl/kontakt/oddzialy-z-obsluga-detaliczna-i-biznesowa"]

    def parse(self, response, **kwargs):
        parsed = urlparse(self.start_urls[0])
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        pois_path = response.xpath(".//script[@type='text/javascript' and contains(@src, '/_js_places/')]/@src").get()
        pois_endpoint = urljoin(base_url, pois_path)
        yield scrapy.Request(pois_endpoint, callback=self.parse_pois)

    def parse_pois(self, response):
        details = chompjs.parse_js_object(response.text)

        for poi in details.get("department_retail_business").values():
            branch = poi.get("basicParameters")
            if not branch.get("branch_id"):
                continue  # Currently 2 don't have ids
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
