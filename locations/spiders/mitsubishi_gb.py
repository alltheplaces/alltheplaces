from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mitsubishi import MitsubishiSpider


class MitsubishiGBSpider(scrapy.Spider):
    name = "mitsubishi_gb"
    item_attributes = MitsubishiSpider.item_attributes
    allowed_domains = ["mitsubishi-motors.co.uk"]
    start_urls = ["https://mitsubishi-motors.co.uk/find-a-dealer/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for dealer in chompjs.parse_js_object(response.xpath('//*[contains(text(),"postalcode")]/text()').get()):
            dealer.update(dealer.pop("basic"))
            dealer.update(dealer["addresses"].pop("visiting_address"))
            item = DictParser.parse(dealer)
            item.pop("email")
            item["street_address"] = merge_address_lines([dealer["street_1"], dealer["street_2"], dealer["street_3"]])
            item["name"] = dealer["marketingname"]
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
