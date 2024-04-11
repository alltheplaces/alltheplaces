from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CostcoGlobalSpider(Spider):
    name = "costco_global"
    item_attributes = {"brand": "Costco", "brand_wikidata": "Q715583"}
    start_urls = [
        "https://www.costco.co.uk/store-finder/search?q=",
        "https://www.costco.com.au/store-finder/search?q=",
        "https://www.costco.com.tw/store-finder/search?q=",
        "https://www.costco.fr/store-finder/search?q=",
        "https://www.costco.is/store-finder/search?q=",
        "https://www.costco.co.jp/store-finder/search?q=",
        "https://www.costco.com.mx/store-finder/search?q=",
        "https://www.costco.co.nz/store-finder/search?q=",
        "https://www.costco.co.kr/store-finder/search?q=",
        "https://www.costco.es/store-finder/search?q=",
        "https://www.costco.se/store-finder/search?q=",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["line1"], location["line2"]])
            item["website"] = response.urljoin(item["website"].removeprefix("/store/").split("?", 1)[0])

            item["ref"] = location["warehouseCode"]

            services = {}
            for service in location.get("availableServices", []):
                services[service["code"]] = service

            for code, cat in [
                # ("FOOD_COURT", Categories.FAST_FOOD),
                ("GAS_STATION", Categories.FUEL_STATION),
                # ("HEARING_AIDS", Categories.SHOP_HEARING_AIDS),
                # ("OPTICAL", Categories.SHOP_OPTICIAN),
                # ("TIRE_CENTER", Categories.SHOP_TYRES),
            ]:
                i = item.deepcopy()
                i["ref"] = "{}_{}".format(item["ref"], code)

                apply_category(cat, i)
                yield i

            apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Available" in location.get("features", []))

            apply_category(Categories.SHOP_WHOLESALE, item)

            yield item
