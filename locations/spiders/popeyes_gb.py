from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class PopeyesGBSpider(Spider):
    name = "popeyes_gb"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}

    start_urls = ["https://pe-uk-ordering-api-fd-eecsdkg6btfeg0cc.z01.azurefd.net/api/v2/restaurants"]


    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            yield item
