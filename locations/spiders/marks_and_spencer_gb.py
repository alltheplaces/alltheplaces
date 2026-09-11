import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MarksAndSpencerGBSpider(CrawlSpider):
    name = "marks_and_spencer_gb"
    item_attributes = {"brand": "Marks & Spencer", "brand_wikidata": "Q714491"}
    start_urls = ["https://www.marksandspencer.com/store-listing"]
    rules = [Rule(LinkExtractor(allow=r"/stores/[^/]+$"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        json_data = DictParser.get_nested_key(
            json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get()), "store"
        )
        item = DictParser.parse(json_data)
        item["branch"] = item.pop("name")
        item["housenumber"] = item.pop("street_address")
        item["street"] = json_data.get("address").get("addressLine2")
        item["website"] = response.url

        if "-bp-" in response.url:
            item["located_in"] = "BP"
            item["located_in_wikidata"] = "Q152057"
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-moto-simply-food-" in response.url:
            item["operator"] = "Moto"
            item["operator_wikidata"] = "Q6917970"
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-welcome-break-" in response.url:
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-simply-food-" in response.url or "-simply-foods-" in response.url:
            item["name"] = "M&S Simply Food"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif "-foodhall-" in response.url:
            item["name"] = "M&S Foodhall"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            if "OUTLET" in item["branch"]:
                item["name"] = "M&S Outlet"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            else:
                item["name"] = "Marks & Spencer"
                apply_category(Categories.GENERIC_SHOP, item)

        facilities = [f["name"] for f in json_data["facilities"]]
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby changing facilities" in facilities)
        apply_yes_no(Extras.PARKING, item, "Car parking" in facilities)
        apply_yes_no(Extras.TOILETS, item, "Toilets" in facilities)

        services = [f["name"] for f in json_data["services"]]
        apply_yes_no(Extras.ATM, item, "Cash machine" in services)
        apply_yes_no(Extras.WIFI, item, "Free Wi-Fi" in services)

        # departments = [f["name"] for f in json_data["departments"]]

        yield item
