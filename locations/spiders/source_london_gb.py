from scrapy import Spider

from locations.dict_parser import DictParser


class SourceLondonGBSpider(Spider):
    name = "source_london_gb"
    item_attributes = {"brand": "Source London", "brand_wikidata": "Q7565133"}
    start_urls = ["https://www.sourcelondon.net/api/infra/location"]

    def parse(self, response, **kwargs):
        for location in response.json():
            yield DictParser.parse(location)
