from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NSLCCASpider(Spider):
    name = "nslc_ca"
    item_attributes = {"brand": "NSLC", "brand_wikidata": "Q17018587"}
    start_urls = ["https://www.mynslc.com/ac/storelocations"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["brand"] = location["banner"]

            item["street_address"] = location["addressInfo"]["address1"]
            item["state"] = location["addressInfo"]["province"]
            item["postcode"] = location["addressInfo"]["postal"]
            item["city"] = location["addressInfo"]["city"]

            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]:
                item["opening_hours"].add_range(day["dayOfWeek"], day["opens"], day["closes"])

            item["website"] = f"https://www.mynslc.com/en/Stores/Store_{location['id']}"

            # TODO: At a later point, tagging for cannabis or primarily cannabis should be explored.
            # for feature in location['features']:
            # if "CP" in feature['feature_id']:
            #    cannabis products

            # if "STN" in feature['feature_id']:
            #    tasting station

            # if "STM" in feature['feature_id']:
            #    ????

            # CLD - Cool Zone?
            # POW - The Port Section?
            # RPS - Product Specialist?
            # FLS - French Language Service

            yield item
