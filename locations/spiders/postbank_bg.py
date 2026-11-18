import json

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PostbankBGSpider(Spider):
    name = "postbank_bg"

    item_attributes = {"brand": "Postbank", "brand_wikidata": "Q7234083", "country": "BG"}

    start_urls = ["https://www.postbank.bg/za-nas/kontakti/lokatsii/"]

    DATASETS = {
        "branch-location-data": Categories.BANK,
        "atm-location-data": Categories.ATM,
    }

    def parse(self, response: TextResponse):
        for element_id, category in self.DATASETS.items():
            data = response.xpath(f'//*[@id="{element_id}"]/text()').get()
            if not data:
                continue

            for location in json.loads(data):
                item = DictParser.parse(location)
                apply_category(category, item)
                yield item
