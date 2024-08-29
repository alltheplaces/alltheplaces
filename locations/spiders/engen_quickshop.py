from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser


class EngenQuickshopSpider(Spider):
    name = "engen_quickshop"
    item_attributes = {
        "brand": "Quickshop",
        "brand_wikidata": "Q122764368",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    start_urls = ["https://engen-admin.engen.co.za/api/service-stations/all"]

    def parse(self, response):
        data = response.json()
        for i in data["response"]["data"]["stations"]:
            if "Quickshop" not in i.get("rental_units", ""):
                continue
            postcode = i.pop("street_postal_code")
            if postcode and postcode != "0":
                i["postcode"] = postcode
            item = DictParser.parse(i)
            yield item
