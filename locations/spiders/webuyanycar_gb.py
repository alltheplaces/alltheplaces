# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser
from locations.google_url import extract_google_position


class WebuyanycarGBSpider(CrawlSpider):
    name = "webuyanycar_gb"
    item_attributes = {"brand": "WeBuyAnyCar", "brand_wikidata": "Q7977432"}
    allowed_domains = ["www.webuyanycar.com"]
    start_urls = ["https://www.webuyanycar.com/branch-locator/"]
    rules = [
        Rule(
            LinkExtractor(allow=".*/branch-locator/.*"), callback="parse", follow=False
        )
    ]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        if item := LinkedDataParser.parse(response, "LocalBusiness"):
            # TODO: street_address needs a structural clean-up approach
            item["ref"] = response.url
            item["country"] = "GB"
            extract_google_position(item, response)
            yield item
