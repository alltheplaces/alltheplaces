import html

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class LewiatanPLSpider(Spider):
    name = "lewiatan_pl"
    item_attributes = {"brand": "Lewiatan", "brand_wikidata": "Q11755396"}
    start_urls = ["https://www.lewiatan.pl/api/stores"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["operator"] = html.unescape(item.pop("name"))
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.urljoin(location["url"])
            if " (" in item["city"]:
                item["city"] = item["city"].split(" (")[0]
            apply_category(Categories.SHOP_SUPERMARKET, item)

            if item.get("phone") == "BRAK":  # 300 x "missing"
                item["phone"] = None

            yield item
