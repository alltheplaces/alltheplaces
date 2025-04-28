from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LaComerMXSpider(JSONBlobSpider):
    name = "la_comer_mx"
    item_attributes = {"brand": "La Comer", "brand_wikidata": "Q134237561"}
    allowed_domains = ["www.lacomer.com.mx"]
    start_urls = [
        "https://www.lacomer.com.mx/lacomer-api/api/v1/public/sucursal/sucursales?succFmt=200&succId=380&tipoNombre="
    ]
    locations_key = ["listLacomer"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["succId"])
        item["branch"] = feature["succDesOri"].removeprefix(self.item_attributes["brand"]).strip()
        item["housenumber"] = feature["succNumext"]
        item["street"] = feature["succCalle"]
        item["city"] = feature["succCol"]
        item["postcode"] = feature["succCp"]
        item["state"] = feature["succEdo"]
        item["lat"] = feature["succLatitud"]
        item["lon"] = feature["succLongitud"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS, *feature["horario"].split(" a ", 1))
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
