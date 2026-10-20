from typing import Iterable

from pyproj import Transformer
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider

ISUZU_SHARED_ATTRIBUTES = {"brand": "Isuzu", "brand_wikidata": "Q29803"}
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")


class IsuzuJPSpider(MapionSpider):
    name = "isuzu_jp"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    allowed_domains = ["sasp.mapion.co.jp"]
    feature_url_template = "https://sasp.mapion.co.jp/b/isuzu_shop/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        lat = data.get("latitude")
        lon = data.get("longitude")
        wgs84_lat, wgs84_lon = TOKYO_TO_WGS84.transform(lat, lon)
        item["lat"] = wgs84_lat
        item["lon"] = wgs84_lon
        item["name"] = None
        if branch := data.get("name"):
            item["branch"] = branch
        if phone := data.get("office_tel"):
            item["phone"] = phone
        if fax := data.get("office_fax"):
            item["extras"]["fax"] = fax

        apply_category(Categories.SHOP_TRUCK, item)

        yield item
