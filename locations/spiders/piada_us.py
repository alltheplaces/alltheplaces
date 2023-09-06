import re

import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class PiadaUSSpider(Spider):
    name = "piada_us"
    item_attributes = {"brand": "Piada Italian Street Food", "brand_wikidata": "Q7190020"}
    start_urls = ["https://mypiada.com/locations"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        for m in re.findall(
            r"stores\.push\((.*?)\)", response.xpath('//script/text()[contains(., "stores.push")]').get(), re.S
        ):
            location = chompjs.parse_js_object(m)

            location["lat"], location["lon"] = location.pop("geo").split(",")
            location["address"] = clean_address(Selector(text=location["address"]).xpath("//text()").getall())
            location["website"] = f'https://mypiada.com/locations/{location["slug"]}'

            yield DictParser.parse(location)
