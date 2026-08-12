from typing import Any, Iterable
from urllib.parse import urljoin

from chompjs import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RohanGBSpider(JSONBlobSpider):
    name = "rohan_gb"
    item_attributes = {"brand": "Rohan", "brand_wikidata": "Q17025822"}
    start_urls = ["https://www.rohan.co.uk/shopfinder/"]

    def extract_json(self, response: Response) -> list[dict]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        return chompjs.parse_js_object(rsc[rsc.index('{"type":"FeatureCollection"') :])["features"]

    def pre_process_data(self, location: dict) -> None:
        location.update(location.pop("properties"))
        location.update(location.pop("address"))
        for key, value in list(location.items()):
            if value == "$undefined":
                location[key] = None

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("email", None)
        item["branch"] = item.pop("name")
        slug = item["branch"].lower().replace(" ", "-")
        item["ref"] = slug
        item["website"] = urljoin("https://www.rohan.co.uk/our-shops/", slug)

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            rule = location["hours"].get(day.lower()) or {}
            if rule.get("open") is True and "$undefined" not in (rule.get("opening"), rule.get("closing")):
                item["opening_hours"].add_range(day, rule["opening"], rule["closing"])

        if (wheelchair := location.get("wheelchair_access")) is not None:
            apply_yes_no(Extras.WHEELCHAIR, item, wheelchair is True, False)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
