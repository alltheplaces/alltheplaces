import re

import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class PiadaUSSpider(Spider):
    name = "piada_us"
    item_attributes = {"brand": "Piada Italian Street Food", "brand_wikidata": "Q7190020"}
    start_urls = ["https://mypiada.com/locations"]

    def parse(self, response, **kwargs):
        for m in re.findall(
            r"stores\.push\((.*?)\)", response.xpath('//script/text()[contains(., "stores.push")]').get(), re.S
        ):
            location = chompjs.parse_js_object(m)
            if "coming soon" in location.get("phone", "").lower():  # coordinates are also incorrect
                continue
            location["lat"], location["lon"] = location.pop("geo").split(",")
            location["address"] = merge_address_lines(Selector(text=location["address"]).xpath("//text()").getall())
            location["website"] = f'https://mypiada.com/locations/{location["slug"]}'

            yield DictParser.parse(location)
