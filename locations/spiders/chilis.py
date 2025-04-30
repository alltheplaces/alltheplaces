from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ChilisSpider(CrawlSpider):
    name = "chilis"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    allowed_domains = ["chilis.com"]
    download_delay = 0.5
    start_urls = ["https://www.chilis.com/locations"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/locations/[a-z]{2}/[-\w]+$"),
        ),
        Rule(
            LinkExtractor(allow=r"/locations/[a-z]{2}/[-\w]+/[-\w]+$"),
        ),
        Rule(LinkExtractor(allow=r"/locations/[a-z]{2}/[-\w]+/[-\w]+/[-\w]+"), callback="parse"),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "Coordinates")]/text()')
            .re_first(r"Address\\\":\[.+?\]")
            .replace("\\", "")
        )[0]
        item = DictParser.parse(location)
        item["ref"] = item["website"] = response.url
        item["street_address"] = merge_address_lines(
            [
                location.get("StreetAddressOne"),
                location.get("StreetAddressTwo"),
                location.get("StreetAddressThree"),
                location.get("StreetAddressFour"),
            ]
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        yield item
