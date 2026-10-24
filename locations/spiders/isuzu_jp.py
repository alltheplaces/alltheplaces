from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider

ISUZU_SHARED_ATTRIBUTES = {"brand": "Isuzu", "brand_wikidata": "Q29803"}


class IsuzuJPSpider(MapionSpider):
    name = "isuzu_jp"
    item_attributes = ISUZU_SHARED_ATTRIBUTES
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "isuzu_shop"
    website_template = "https://sasp.mapion.co.jp/b/isuzu_shop/info/{}/"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        if branch := data.get("name"):
            item["branch"] = branch
        if phone := data.get("office_tel"):
            item["phone"] = phone
        if fax := data.get("office_fax"):
            item["extras"]["fax"] = fax

        apply_category(Categories.SHOP_TRUCK, item)

        yield item
