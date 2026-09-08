from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class NttLePercJPSpider(MapionSpider):
    name = "ntt_le_perc_jp"
    item_attributes = {"brand": "NTTル・パルク", "brand_wikidata": "Q11236111"}
    allowed_domains = ["sasp.mapion.co.jp"]
    feature_url_template = "https://sasp.mapion.co.jp/b/leperc/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["phone"] = None
        item["name"] = None
        if car_count := data.get("car_count"):
            item["extras"]["capacity"] = car_count

        apply_category(Categories.PARKING, item)
        item["extras"]["fee"] = "yes"

        yield item
