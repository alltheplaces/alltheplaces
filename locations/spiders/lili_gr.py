import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_GR, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LiliGRSpider(JSONBlobSpider):
    name = "lili_gr"
    item_attributes = {"brand": "Lili", "brand_wikidata": "Q111764460"}
    start_urls = ["https://lilidrogerie.gr/extension/module/locations_map"]

    def extract_json(self, response: Response) -> Any:
        script = response.xpath('//script[contains(text(), "const locations = ")]/text()').get()
        return chompjs.parse_js_object(script.split("const locations = ", 1)[1])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^Lili( Drogerie)?( -)?\s*", "", item.pop("name").split(" | ")[0]).strip()
        item["opening_hours"] = OpeningHours()
        for segment in (feature.get("open") or "").split("|"):
            item["opening_hours"].add_ranges_from_string(segment, days=DAYS_GR)
        apply_category(Categories.SHOP_CHEMIST, item)
        yield item
