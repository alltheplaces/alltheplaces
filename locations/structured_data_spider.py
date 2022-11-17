import re

from scrapy import Spider

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


def extract_email(item, response):
    for link in response.xpath("//a[contains(@href, 'mailto')]/@href").getall():
        link = link.strip()
        if link.startswith("mailto:"):
            item["email"] = link.replace("mailto:", "")
            return


def extract_phone(item, response):
    for link in response.xpath("//a[contains(@href, 'tel')]/@href").getall():
        link = link.strip()
        if link.startswith("tel:"):
            item["phone"] = link.replace("tel:", "")
            return


def extract_twitter(item, response):
    if twitter := response.xpath('//meta[@name="twitter:site"]/@content').get():
        twitter = twitter.strip()
        if not twitter == "@":
            item["twitter"] = twitter


def extract_image(item, response):
    if image := response.xpath('//meta[@name="twitter:image"]/@content').get():
        item["image"] = image.strip()
        return
    if image := response.xpath('//meta[@name="og:image"]/@content').get():
        item["image"] = image.strip()


def get_url(response) -> str:
    if canonical := response.xpath('//link[@rel="canonical"]/@href').get():
        return canonical
    return response.url


class StructuredDataSpider(Spider):
    wanted_types = [
        "LocalBusiness",
        "ConvenienceStore",
        "Store",
        "Restaurant",
        "BankOrCreditUnion",
        "GroceryStore",
        "FastFoodRestaurant",
        "Hotel",
        "Place",
        "ClothingStore",
        "DepartmentStore",
        "HardwareStore",
        "AutomotiveBusiness",
        "BarOrPub",
    ]
    search_for_email = True
    search_for_phone = True
    search_for_twitter = True
    search_for_image = True
    parse_json_comments = False

    def parse_sd(self, response):
        MicrodataParser.convert_to_json_ld(response)
        for wanted_type in self.wanted_types:
            if ld_item := LinkedDataParser.find_linked_data(
                response, wanted_type, parse_json5=self.parse_json_comments
            ):
                self.pre_process_data(ld_item)

                item = LinkedDataParser.parse_ld(ld_item)

                url = get_url(response)

                if item["ref"] is None:
                    if hasattr(self, "rules"):
                        # Attempt to pull a match from CrawlSpider.rules
                        for rule in getattr(self, "rules"):
                            for allow in rule.link_extractor.allow_res:
                                if match := re.match(allow, url):
                                    if len(match.groups()) > 0:
                                        item["ref"] = match.group(1)
                    elif hasattr(self, "sitemap_rules"):
                        # Attempt to pull a match from SitemapSpider.sitemap_rules
                        for rule in getattr(self, "sitemap_rules"):
                            if match := re.match(rule[0], url):
                                if len(match.groups()) > 0:
                                    item["ref"] = match.group(1)

                    if item["ref"] is None:
                        item["ref"] = url

                item["website"] = None
                if isinstance(item["website"], list):
                    item["website"] = item["website"][0]

                if not item["website"]:
                    item["website"] = url
                elif item["website"].startswith("www"):
                    item["website"] = "https://" + item["website"]

                if self.search_for_email and item["email"] is None:
                    extract_email(item, response)

                if self.search_for_phone and item["phone"] is None:
                    extract_phone(item, response)

                if self.search_for_twitter and item.get("twitter") is None:
                    extract_twitter(item, response)

                if self.search_for_image and item.get("image") is None:
                    extract_image(item, response)

                yield from self.post_process_item(item, response, ld_item)

    def parse(self, response, **kwargs):
        yield from self.parse_sd(response)

    def pre_process_data(self, ld_data, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item, response, ld_data, **kwargs):
        """Override with any post-processing on the item."""
        yield from self.inspect_item(item, response)

    def inspect_item(self, item, response):
        """Deprecated, please use post_process_item(self, item, response, ld_data):"""
        yield item
