from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class ChilisSpider(CrawlSpider):
    name = "chilis"
    item_attributes = {"brand": "Chili's", "brand_wikidata": "Q1072948"}
    allowed_domains = ["chilis.com"]
    start_urls = ["https://www.chilis.com/locations"]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,  # Avoid http 429 error
        "DOWNLOAD_DELAY": 3,
    }
    rules = [
        Rule(
            LinkExtractor(allow=r"/locations/[a-z]{2}/[-\w]+$"),
        ),
        Rule(
            LinkExtractor(
                allow=r"/locations/[a-z]{2}/[-\w]+/[-\w]+$",
            ),
            callback="parse",  # Parse locations from city page, rather than from individual POI pages because some of the urls actually don't work
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "currentCityMergedData")]/text()')
            .re_first(r"currentCityMergedData\\\":\[.+\]")
            .replace("\\", "")
        ):
            item = DictParser.parse(location)
            item["ref"] = location.get("restaurantId")
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines(
                [location.get("streetaddress"), location.get("streetaddress2")]
            )
            item["website"] = f'{response.url.strip("/")}/{location["slug"]}'
            yield item
