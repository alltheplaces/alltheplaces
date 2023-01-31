from scrapy import Spider

from locations.dict_parser import DictParser


class CousinsSubsUSSpider(Spider):
    name = "cousins_subs_us"
    item_attributes = {"brand": "Cousins Subs", "brand_wikidata": "Q5178843"}
    start_urls = ["https://www.cousinssubs.com/api/restaurant/"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["website"] = f'https://www.cousinssubs.com/order/{location["slug"]}'
            location["street_address"] = location.pop("street")

            yield DictParser.parse(location)
