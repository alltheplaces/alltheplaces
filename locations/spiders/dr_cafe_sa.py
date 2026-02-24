import re

import chompjs
from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class DrCafeSASpider(Spider):
    name = "dr_cafe_sa"
    item_attributes = {"brand": "د.كيف", "brand_wikidata": "Q105714225"}
    start_urls = ["https://www.drcafe.com/en-intl/GoogleMapStores"]
    no_refs = True

    def parse(self, response, **kwargs):
        data = re.search(r"var markers = .*(\[.*\])", response.json().get("ListOfGoogleMap")).group(0)
        for store in chompjs.parse_js_object(data):
            store["address"] = store.pop("Country")
            item = DictParser.parse(store)
            title = store["title"]
            item["branch"] = title.split("|")[0].strip()
            apply_category(Categories.COFFEE_SHOP, item)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in title)
            yield item
