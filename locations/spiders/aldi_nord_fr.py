from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class AldiNordFRSpider(Spider):
    name = "aldi_nord_fr"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    start_urls = [
        "https://uberall.com/api/storefinders/ALDINORDFR_Mmljd17th8w26DMwOy4pScWk4lCvj5/locations/all"
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["response"]["locations"]:

            store["street_address"] = ", ".join(
                filter(None, [store.pop("streetAndNumber", store.pop("addressExtra"))])
            )

            item = DictParser.parse(store)

            oh = OpeningHours()
            for rule in store["openingHours"]:
                if rule.get("closed", False):
                    continue
                oh.add_range(DAYS[rule["dayOfWeek"] - 1], rule["from1"], rule["to1"])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
