from scrapy import Spider

from locations.dict_parser import DictParser


class OspreyGBSpider(Spider):
    name = "osprey_gb"
    item_attributes = {"brand": "Osprey", "brand_wikidata": "Q117706577"}
    start_urls = [
        "https://apigw.ospreycharging.co.uk/portal/location/map?filter=box(coordinates,-90.0,-180.0,90.0,180.0)%E2%88%A7evses.status%E2%88%89%7BREMOVED%7D"
    ]

    def parse(self, response, **kwargs):
        for location in response.json():
            yield DictParser.parse(location)
