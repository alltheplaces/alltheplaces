import json
import re

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class EwmGBIESpider(JSONBlobSpider):
    name = "ewm_gb_ie"
    item_attributes = {"brand": "The Edinburgh Woollen Mill", "brand_wikidata": "Q16834657"}
    start_urls = ["https://www.ewm.co.uk/store-finder"]

    def parse(self, response):
        match = re.search(r"storelocator.sources = ([^\n]+)", response.text)
        data = match.group(1)[:-1]
        json_data = json.loads(data)
        for location in json_data:
            item = DictParser.parse(location)
            item["addr_full"] = (
                location["links"]["showOnMap"]
                .replace('<a target="_blank" href="//maps.google.com/maps?q=', "")
                .replace('">Show on Google Map</a>', "")
            )
            item["branch"] = item.pop("name").removeprefix("The Edinburgh Woollen Mill, ")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
