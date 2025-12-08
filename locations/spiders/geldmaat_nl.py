from urllib.parse import urlencode, urljoin

from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class GeldmaatNLSpider(Spider):
    name = "geldmaat_nl"
    # Opening hours unfortunately seem to be sent only in the detail pop-up,
    # so fetching them would require sending 1 extra request per each ATM.

    item_attributes = {"brand": "Geldmaat", "brand_wikidata": "Q74051230"}

    located_in_brands = {
        "ako": {"brand": "AKO", "brand_wikidata": "Q2159963"},
        "albertheijn": {"brand": "Albert Heijn", "brand_wikidata": "Q1653985"},
        "blokker": {"brand": "Blokker", "brand_wikidata": "Q33903645"},
        "bruna": {"brand": "Bruna", "brand_wikidata": "Q3317555"},
        "cigo": {"brand": "Cigo", "brand_wikidata": "Q62391977"},
        "dekamarkt": {"brand": "Dekamarkt", "brand_wikidata": "Q2489350"},
        "primera": {"brand": "Primera", "brand_wikidata": "Q2176149"},
        "geldmaat": {"brand": "Geldmaat", "brand_wikidata": "Q74051230"},
        "readshop": {"brand": "The Readshop", "brand_wikidata": "Q114905224"},
        "spar": {"brand": "Spar", "brand_wikidata": "Q610492"},
    }

    FUNCTIONALITY_MAPPING = {
        "Geldautomaat": Extras.CASH_OUT,
        "Geld storten en opnemen": Extras.CASH_IN,
        # Can be added once tagged correctly
        # "Muntrol-automaat": "coins_out",
        # "Muntstortautomaat": "coins_in",
        # "Sealbagautomaat": "sealbag",
    }

    api_url = "https://api.prod.locator-backend.geldmaat.nl/locations"
    start_urls = [api_url]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)

            for functionality, tag in self.FUNCTIONALITY_MAPPING.items():
                apply_yes_no(tag, item, functionality in location["functionality"], tag == Extras.CASH_OUT)

            # all cash-in ATMs are also cash-out ATMs
            apply_yes_no(Extras.CASH_OUT, item, "Geld storten en opnemen" in location["functionality"], True)

            apply_yes_no("speech_output", item, location["audioGuidance"], False)

            if (store_type := location["storeType"]) not in ["n/a", "generic"]:
                if store_brand := self.located_in_brands.get(store_type):
                    item["located_in"] = store_brand["brand"]
                    item["located_in_wikidata"] = store_brand["brand_wikidata"]
                else:
                    item["located_in"] = store_type

            yield item

        if "token" in response.json():
            yield Request(urljoin(self.api_url, "?" + urlencode(dict(token=response.json()["token"]))))
