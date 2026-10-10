import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YazigiBRSpider(StructuredDataSpider):
    name = "yazigi_br"
    item_attributes = {"brand": "Yázigi", "brand_wikidata": "Q10394813"}
    start_urls = ["https://escolas.yazigi.com.br/"]
    wanted_types = ["LocalBusiness"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for url in re.findall(r'\\"siteUrl\\":\\"(https://escolas\.yazigi\.com\.br/[^\\"]+)\\"', response.text):
            yield Request(url, callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item.pop("image", None)
        item["branch"] = item.pop("name").removeprefix("YÁZIGI ").title()
        apply_category(Categories.LANGUAGE_SCHOOL, item)
        yield item
