# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser
from locations.google_url import url_to_coords


def extract_google_position(item, response):
    for link in response.xpath("//iframe/@src").extract():
        if "google.com" in link:
            item["lat"], item["lon"] = url_to_coords(link)
            return


class WrenKitchensGBSpider(CrawlSpider):
    name = "wrenkitchens_gb"
    item_attributes = {"brand": "Wren Kitchens", "brand_wikidata": "Q8037744"}
    allowed_domains = ["wrenkitchens.com"]
    start_urls = ["https://www.wrenkitchens.com/showrooms/"]
    rules = [Rule(LinkExtractor(allow="/showrooms/"), callback="parse", follow=False)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        if item := LinkedDataParser.parse(response, "HomeAndConstructionBusiness"):
            item["ref"] = response.url
            item["country"] = "GB"
            extract_google_position(item, response)
            yield item
