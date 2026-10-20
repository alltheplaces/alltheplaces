from typing import Iterable

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class LaCasaDeLasCarcasasESSpider(StoremapperSpider):
    name = "la_casa_de_las_carcasas_es"
    item_attributes = {"brand": "La Casa de las Carcasas", "brand_wikidata": "Q127275290"}
    company_id = "33747-4AsOaVgWvn2ItT2p"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("LA CASA DE LAS CARCASAS ", "")
        oh = OpeningHours()
        for day_time in location.get("store_business_hours"):
            open_time = day_time.get("open_time")
            close_time = day_time.get("close_time")
            oh.add_range(day=DAYS_FULL[int(day_time.get("week_day")) - 1], open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
