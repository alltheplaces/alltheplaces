import json

from scrapy import Spider

from locations.dict_parser import DictParser


class FastShiftAmSpider(Spider):
    name = "fast_shift_am"
    item_attributes = {"brand": "Fast Shift", "brand_wikidata": "Q118289125"}
    start_urls = [
        "https://www.fastshift.am/en/%D5%B4%D5%A1%D5%BD%D5%B6%D5%A1%D5%B3%D5%B5%D5%B8%D6%82%D5%B2%D5%A5%D6%80-%D5%BF%D5%A5%D6%80%D5%B4%D5%AB%D5%B6%D5%A1%D5%AC%D5%B6%D5%A5%D6%80"
    ]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//@data-params").get())["fields"]:
            loc = {}
            for k, v in location["params"]["vars"].items():
                loc[k] = v["value"]
            yield DictParser.parse(loc)
