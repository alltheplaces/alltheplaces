from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class FujiyaJPSpider(MapionSpider):
    name = "fujiya_jp"
    item_attributes = {"brand": "不二家", "brand_wikidata": "Q858452"}
    allowed_domains = ["shop.fujiya-peko.co.jp"]
    feature_url_template = "https://shop.fujiya-peko.co.jp/b/fujiya/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = (
            data.get("name")
            .removeprefix("ペコちゃんmilkyドーナツ")
            .removeprefix("milky70 since1951")
            .removeprefix("ペコちゃんmilkyタイム")
            .lstrip()
        )
        item["phone"] = f"+81 {data.get('tel1')}-{data.get('tel2')}-{data.get('tel3')}"
        if (open_time := f"{data.get('openhour1')}:{data.get('openmin1')}") and (
            close_time := f"{data.get('closehour1')}:{data.get('closemin1')}"
        ):
            oh = OpeningHours()
            oh.add_days_range(DAYS, open_time, close_time)
            item["opening_hours"] = oh
        if data.get("flag4"):  # flag4 is for sit-down restaurants. they sell confectionery as well
            apply_category(Categories.RESTAURANT, item)
        apply_category(Categories.SHOP_CONFECTIONERY, item)

        yield item
