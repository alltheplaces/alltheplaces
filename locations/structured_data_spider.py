from scrapy import Spider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class StructuredDataSpider(Spider):

    wanted_types = []
    search_for_email = True
    search_for_phone = True

    def parse_sd(self, response):
        MicrodataParser.convert_to_json_ld(response)
        for wanted_type in self.wanted_types:
            if item := LinkedDataParser.parse(response, wanted_type):

                if item["ref"] is None:
                    item["ref"] = response.url

                if self.search_for_email:
                    self.email_search(item, response)

                if self.search_for_phone and item["phone"] is None:
                    self.phone_search(item, response)

                for i in self.inspect_item(item, response):
                    yield i

    def inspect_item(self, item, response):
        yield item

    def email_search(self, item, response):
        for link in response.xpath("//a[contains(@href, 'mailto')]/@href").getall():
            link = link.strip()
            if link.startswith("mailto:"):
                if not item.get("extras"):
                    item["extras"] = {}

                item["extras"]["email"] = link.replace("mailto:", "")
                return

    def phone_search(self, item, response):
        for link in response.xpath("//a[contains(@href, 'tel')]/@href").getall():
            link = link.strip()
            if link.startswith("tel:"):

                item["phone"] = link.replace("tel:", "")
                return
