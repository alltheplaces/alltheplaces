import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_NO, OpeningHours, sanitise_day


class CoopNOSpider(scrapy.Spider):
    name = "coop_no"
    BRANDS = {
        "01": {"brand": "Coop Prix", "brand_wikidata": "Q5167705"},
        "02": {"brand": "Obs", "brand_wikidata": "Q5167707"},
        "03": {"brand": "Coop Mega", "brand_wikidata": "Q4581010"},
        "04": {"brand": "Coop Marked", "brand_wikidata": "Q5167703"},
        "07": {"brand": "Extra", "brand_wikidata": "Q11964085"},
        "08": {"brand": "Matkroken", "brand_wikidata": "Q11988679"},
        "41": {"brand": "Coop Byggmix", "brand_wikidata": "Q12714075"},
        "43": {"brand": "Obs BYGG", "brand_wikidata": "Q5167707"},
        "45": {"brand": "Coop Elektro", "brand_wikidata": "Q111534601"},
    }
    start_urls = [
        "https://coop.no/StoreService/StoresByBoundingBox?locationLat=0&locationLon=0&latNw=90&lonNw=-180&latSe=-90&lonSe=180"
    ]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("Address")
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for rule in location["OpeningHours"]:
                if rule["Closed"]:
                    continue
                if day := sanitise_day(rule["Day"], DAYS_NO):
                    start_time, end_time = rule["OpenString"].split("-")
                    item["opening_hours"].add_range(day, start_time[:5], end_time[:5])

            if brand := self.BRANDS.get(location["ChainId"]):
                item.update(brand)

            yield item
