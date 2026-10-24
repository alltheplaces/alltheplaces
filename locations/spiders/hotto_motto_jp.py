from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class HottoMottoJPSpider(MapionSpider):
    name = "hotto_motto_jp"
    item_attributes = {"brand": "ほっともっと", "brand_wikidata": "Q10850949"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "hottomotto_display"
    website_template = "https://store.hottomotto.com/b/hottomotto/info/{}/"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = data.get("name").removeprefix("ほっともっと").lstrip()
        apply_category(Categories.FAST_FOOD, item)

        yield item
