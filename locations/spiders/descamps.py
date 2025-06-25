from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.inno_be import InnoBESpider
from locations.spiders.printemps import PrintempsSpider


class DescampsSpider(Spider):
    name = "descamps"
    item_attributes = {"brand": "Descamps", "brand_wikidata": "Q91002058"}
    allowed_domains = ["www.descamps.com"]
    start_urls = ["https://www.descamps.com/externalgateway/api/external/stores/stores-by-brand-id?brandId=1"]

    _located_in_brands = {
        "GALERIES LAFAYETTE": {"brand": "Galeries Lafayette", "brand_wikidata": "Q3094686"},
        "INNO": InnoBESpider.item_attributes,
        "PRINTEMPS": PrintempsSpider.item_attributes,
    }

    def parse(self, response: Response) -> Iterable[Feature]:
        for country in response.json():
            for city in country["cities"]:
                for store in city["stores"]:
                    item = DictParser.parse(store)
                    item["ref"] = store["storeCode"]
                    item.pop("name", None)
                    item["street_address"] = item.pop("addr_full", None)
                    if item["email"]:
                        item["email"] = item["email"].removesuffix(">")
                    for brand_key, brand_attributes in self._located_in_brands.items():
                        if store["storeShortName"].startswith(f"{brand_key} "):
                            item["located_in"] = brand_attributes["brand"]
                            item["located_in_wikidata"] = brand_attributes["brand_wikidata"]
                            break
                    item["opening_hours"] = OpeningHours()
                    for day_number, day_hours in enumerate(store["openingHours"].split(";")[0:7]):
                        if not day_hours:
                            item["opening_hours"].set_closed(DAYS[day_number])
                        elif len(day_hours.split("|")) == 4:
                            item["opening_hours"].add_range(
                                DAYS[day_number], day_hours.split("|")[0], day_hours.split("|")[1]
                            )
                            item["opening_hours"].add_range(
                                DAYS[day_number], day_hours.split("|")[2], day_hours.split("|")[3]
                            )
                        elif len(day_hours.split("|")) == 2:
                            item["opening_hours"].add_range(
                                DAYS[day_number], day_hours.split("|")[0], day_hours.split("|")[1]
                            )
                    apply_category(Categories.SHOP_HOUSEHOLD_LINEN, item)
                    yield item
