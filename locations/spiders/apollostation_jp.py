from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class ApollostationJPSpider(MapionSpider):
    name = "apollostation_jp"
    item_attributes = {"brand": "apollostation", "brand_wikidata": "Q114731101"}
    allowed_domains = ["map.idemitsu.com"]
    feature_url_template = "https://map.idemitsu.com/b/a/attr/?t=attr_con&kind=0&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = data.get("name")
        apply_yes_no(
            Fuel.ELECTRIC, item, (data.get("has_ev_charger_fast") == "1") or (data.get("has_ev_charger_normal") == "1")
        )
        apply_category(Categories.FUEL_STATION, item)

        yield item
