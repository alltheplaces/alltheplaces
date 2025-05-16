import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS_BR, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BretasBRSpider(JSONBlobSpider):
    name = "bretas_br"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"REST-Range": "resources=0-500"}}
    start_urls = [
        "https://www.bretas.com.br/api/dataentities/LJ/search/?_fields=storeName,address,complement,city,state,businessHours,phone,storeType,storeLink,zipCode,city,state"
    ]
    no_refs = True

    my_brands = {
        "Armazém": {"brand": "Bretas Armazém", "brand_wikidata": "Q19608060"},
        "Atacarejo": {"brand": "Bretas Atacarejo", "brand_wikidata": "Q19608060"},
        "POSTO": {"brand": "Bretas Posto", "brand_wikidata": "Q19608060"},
        "Posto": {"brand": "Bretas Posto", "brand_wikidata": "Q19608060"},
        "Supermercado": {"brand": "Bretas Supermercado", "brand_wikidata": "Q19608060"},
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.update(self.my_brands.get(feature["storeType"]))
        if feature["storeType"] == "Posto" or feature["storeType"] == "POSTO":
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        item["lat"], item["lon"] = url_to_coords(feature["storeLink"])
        oh = OpeningHours()
        for start_day, end_day, start_time, end_time in re.findall(
            r"(\w+) [ae] (\w+) - (\d\d:\d\d) às (\d\d:\d\d)",
            feature["businessHours"].replace("Feriados", "Domingos"),
        ):
            start_day = sanitise_day(start_day, DAYS_BR)
            end_day = sanitise_day(end_day, DAYS_BR)
            if start_day and end_day:
                for day in day_range(start_day, end_day):
                    oh.add_range(day, start_time, end_time)
        item["opening_hours"] = oh
        yield item
