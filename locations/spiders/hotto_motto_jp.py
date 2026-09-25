from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class HottoMottoJPSpider(MapionSpider):
    name = "hotto_motto_jp"
    item_attributes = {"brand": "ほっともっと", "brand_wikidata": "Q10850949"}
    allowed_domains = ["store.hottomotto.com"]
    feature_url_template = "https://store.hottomotto.com/b/hottomotto/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = data.get("name").removeprefix("ほっともっと ")
        apply_category(Categories.FAST_FOOD, item)

        yield item
