from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class NipponRentacarJPSpider(MapionSpider):
    name = "nippon_rentacar_jp"
    item_attributes = {"brand": "ニッポンレンタカー", "brand_wikidata": "Q11086533"}
    allowed_domains = ["store.nipponrentacar.co.jp"]
    feature_url_template = "https://store.nipponrentacar.co.jp/b/nrs/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = "ニッポンレンタカー"
        item["branch"] = data.get("name")
        if yomi := data.get("poi_name_yomi"):
            item.set_tag("branch:ja-Hira", yomi.split("[")[0])
        if eng_name := data.get("ww_name_yomi"):
            item.set_tag("branch:en", eng_name)
        item["addr_full"] = "".join(part for part in (data.get("address1"), data.get("address2")) if part)
        apply_category(Categories.CAR_RENTAL, item)

        yield item
