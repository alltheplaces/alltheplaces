import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


# Does have Linked Data, but requires JS to load it
class AldiNordDKSpider(scrapy.Spider):
    name = "aldi_nord_dk"
    item_attributes = {"brand": "ALDI", "brand_wikidata": "Q41171373"}
    start_urls = [
        "https://uberall.com/api/storefinders/ALDINORDDK_X4Jlb165jBUstmddaEYk5GcxWffPqd/locations/all"
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
