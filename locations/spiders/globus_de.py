from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlobusDESpider(JSONBlobSpider):
    name = "globus_de"
    item_attributes = {"brand": "Globus", "brand_wikidata": "Q457503"}
    allowed_domains = ["globus.de"]
    locations_key = "data"

    async def start(self) -> AsyncIterator[Request]:
        yield FormRequest("https://www.globus.de/api/open", formdata={"type": "maerkte"})

    def pre_process_data(self, feature: dict) -> None:
        rename = {
            "laengengrad": "longitude",
            "breitengrad": "latitude",
            "marktName": "name",
            "strasse": "street_address",
            "plz": "postcode",
            "stadt": "city",
            "telefon": "phone",
            "marktUrl": "website",
            "bundesland": "state",
        }
        del feature["region"]
        for de, en in rename.items():
            feature[en] = feature.pop(de)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        categories = {
            "ARC": Categories.SHOP_WHOLESALE,
            "GC": Categories.SHOP_BEVERAGES,
            "RES": Categories.RESTAURANT,
            "SBW": Categories.SHOP_SUPERMARKET,
            "TS": Categories.FUEL_STATION,
            "WS": Categories.CAR_WASH,
        }
        apply_category(categories[feature["betriebsstaette"]], item)
        item["extras"]["contact:maps"] = feature["googleUrl"]
        item["branch"] = item.pop("name")
        yield item
