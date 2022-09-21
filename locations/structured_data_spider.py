from scrapy import Spider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class StructuredDataSpider(Spider):

    wanted_types = []

    def parse_sd(self, response):
        MicrodataParser.convert_to_json_ld(response)
        for wanted_type in self.wanted_types:
            if item := LinkedDataParser.parse(response, wanted_type):

                if item["ref"] is None:
                    item["ref"] = response.url

                self.inspect_item(item, response)

                yield item

    def inspect_item(self, item, response):
        yield item
