import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.vapestore_gb import clean_address


class PoundlandSpider(scrapy.Spider):
    name = "poundland"
    item_attributes = {"brand": "Poundland", "brand_wikidata": "Q1434528"}
    start_urls = [
        "https://www.poundland.co.uk/rest/poundland/V1/locator/?searchCriteria[scope]=store-locator&searchCriteria[current_page]=1&searchCriteria[page_size]=10000"
    ]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def parse(self, response):
        # We may have to handle pagination at some point
        for store in response.json()["locations"]:
            item = DictParser.parse(store)

            item["street_address"] = clean_address(store["address"].get("line"))

            # "store_id" seems to be a better ref than "id"
            item["ref"] = store.get("store_id")
            item["website"] = "https://www.poundland.co.uk/store-finder/store_page/view/id/" + item["ref"] + "/"

            oh = OpeningHours()
            for rule in store["opening_hours"]:
                if rule["hours"] == "Closed":
                    continue
                open_time, close_time = rule["hours"].split(" - ")
                oh.add_range(rule["day"][:2], open_time, close_time)

            item["opening_hours"] = oh

            apply_yes_no(Extras.ATM, item, store.get("atm") == "1")
            item["extras"]["icestore"] = "yes" if store.get("icestore") == "1" else "no"

            if store["is_pep_co_only"] == "1":
                item["brand"] = "Pep&Co"
                item["brand_wikidata"] = "Q24908166"
            else:
                if store.get("pepshopinshop") == "1":
                    # Pep and Poundland at this location
                    pep = item.copy()

                    pep["ref"] = pep["ref"] + "_pep"

                    pep["brand"] = "Pep&Co"
                    pep["brand_wikidata"] = "Q24908166"

                    pep["located_in"] = self.item_attributes["brand"]
                    pep["located_in_wikidata"] = self.item_attributes["brand_wikidata"]

                    yield pep

            yield item
