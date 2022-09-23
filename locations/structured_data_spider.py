import re

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
                    if hasattr(self, "rules"):
                        # Attempt to pull a match from CrawlSpider.rules
                        for rule in getattr(self, "rules"):
                            for allow in rule.link_extractor.allow_res:
                                if match := re.match(allow, response.url):
                                    if len(match.groups()) > 0:
                                        item["ref"] = match.group(1)
                    elif hasattr(self, "sitemap_rules"):
                        # Attempt to pull a match from SitemapSpider.sitemap_rules
                        for rule in getattr(self, "sitemap_rules"):
                            if match := re.match(rule[0], response.url):
                                if len(match.groups()) > 0:
                                    item["ref"] = match.group(1)

                    if item["ref"] is None:
                        item["ref"] = response.url

                if self.search_for_email and item["email"] is None:
                    self.email_search(item, response)

                if self.search_for_phone and item["phone"] is None:
                    self.phone_search(item, response)

                yield from self.inspect_item(item, response)

    def inspect_item(self, item, response):
        """Override with any additional processing on the item."""
        yield item

    def email_search(self, item, response):
        for link in response.xpath("//a[contains(@href, 'mailto')]/@href").getall():
            link = link.strip()
            if link.startswith("mailto:"):
                item["email"] = link.replace("mailto:", "")
                return

    def phone_search(self, item, response):
        for link in response.xpath("//a[contains(@href, 'tel')]/@href").getall():
            link = link.strip()
            if link.startswith("tel:"):

                item["phone"] = link.replace("tel:", "")
                return
