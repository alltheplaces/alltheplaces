import json
import re
from urllib.parse import urljoin

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class StcSESpider(scrapy.Spider):
    name = "stc_se"
    item_attributes = {"brand": "STC", "brand_wikidata": "Q115114066"}
    start_urls = ["https://www.stc.se/gym"]

    def parse(self, response):
        raw_data = chompjs.parse_js_object(response.xpath('//*[contains(text(),"clubsData")]/text()').get())[1]
        for club in json.loads(re.search(r"clubsData\":(\[.*\]),\"clubTypeInformation", raw_data).group(1)):
            item = DictParser.parse(club)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["website"] = urljoin("https://www.stc.se/gym/", club["slug"])
            apply_category(Categories.GYM, item)
            yield item
