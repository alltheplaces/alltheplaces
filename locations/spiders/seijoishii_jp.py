import json
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SeijoishiiJPSpider(LocationCloudSpider):
    name = "seijoishii_jp"
    item_attributes = {"brand": "成城石井", "brand_wikidata": "Q11495410"}
    api_endpoint = "https://shop.seijoishii.com/seijoishii/api/proxy2/shop/list"
    website_formatter = "https://shop.seijoishii.com/seijoishii/spot/detail?code={}"

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] != "03":
            return  # skip other types

        script = response.xpath('//script[contains(text(), "var spotDetailBean")]/text()').get()
        detail = parse_js_object(script.split("var spotDetailBean = ", 1)[1])
        flags = detail["flags"]
        apply_yes_no(Extras.PARKING, item, flags.get("00021", {}).get("value") == "true")
        apply_yes_no(Extras.DELIVERY, item, flags.get("00023", {}).get("value") == "true")

        for section in detail["detailColumns"]:
            for field in section.get("columns", {}).get("text", []):
                if field["code"] == "00005":
                    hours = json.loads(field["value"])
                    item["opening_hours"] = oh = OpeningHours()
                    for day in DAYS_FULL:
                        if times := [rule["time"] for rule in hours[day.lower()]["times"] if "time" in rule]:
                            for time in times:
                                oh.add_range(day, time["start"][:5], time["end"][:5])
                        else:
                            oh.set_closed(day)

        yield item

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = source_feature["name"]
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
        item["phone"] = f"+81 {source_feature['phone']}"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
