import re
from typing import Any, Iterable

import scrapy
from scrapy.http import Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.subway import SubwaySpider
from locations.structured_data_spider import StructuredDataSpider


class SubwaySouthAmericaSpider(CrawlSpider, StructuredDataSpider):
    name = "subway_south_america"
    item_attributes = SubwaySpider.item_attributes
    allowed_domains = ["restaurantes.subway.com", "subway.business.monster"]
    start_urls = ["https://restaurantes.subway.com/"]
    rules = [
        Rule(LinkExtractor(allow=r"https://restaurantes.subway.com/[a-z-]+"), callback="parse"),
    ]
    wanted_types = ["LocalBusiness"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in re.findall(
            r"siteUrl\":\"(https://restaurantes\.subway\.com/[a-z-0-9]+)\"",
            response.xpath('//*[contains(text(),"address")]/text()').get().replace("\\", ""),
        ):
            yield scrapy.Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").split("-")[1].replace(" - Restaurante Fast-Food", "")
        item["image"] = None
        apply_category(Categories.FAST_FOOD, item)
        yield item
