from typing import Iterable
from chompjs import parse_js_object

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class TokyoHigashiShinkinBankJPSpider(LocationCloudSpider):
    name = "tokyo_higashi_shinkin_bank_jp"
    item_attributes = {
        "brand": "東京東信用金庫",
        "brand_wikidata": "Q11524925",
        "extras": {"brand:en": "Tokyo Higashi Shinkin Bank"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/higashin/api/proxy2/shop/list"
    additional_args = "&category=01.02.03.04"
    website_formatter = "https://pkg.navitime.co.jp/higashin/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        if phone := source_feature.get("phone"):
            if phone != "－":
                item["phone"] = phone

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.BANK, item)
            case "03":
                apply_category(Categories.ATM, item)
            case "04":
                apply_category(Categories.OFFICE_FINANCIAL, item)
            case _:
                return

        item["branch"] = source_feature.get("name", "")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        yield item
def parse_detail_page(self, response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        blob = response.xpath('//script[contains(text(), "var spotDetailBean")]/text()').get()
        if not blob:
            yield item
            return

        fields = {
            entry["code"]: entry["value"]
            for section in parse_js_object(blob.split("var spotDetailBean = ", 1)[1])["detailColumns"]
            for entries in section["columns"].values()
            for entry in entries
        }

        counter, atm = OpeningHours(), OpeningHours()
        # 00006 (祝日/PH) is skipped: OpeningHours has no way to express holiday-only hours.
        for code, hours, days in (
            ("00002", counter, DAYS_WEEKDAY),
            ("00003", atm, DAYS_WEEKDAY),
            ("00004", atm, ["Sa"]),
            ("00005", atm, ["Su"]),
        ):
            value = fields.get(code)
            if value in (None, "－", "非稼動"):
                continue
            for time_range in value.split("/"):
                open_time, close_time = time_range.split("～")
                hours.add_days_range(days, open_time.strip(), close_time.strip())

        if counter:
            item["opening_hours"] = counter
        if atm:
            if source_feature["categories"][0]["code"] == "03":
                item["opening_hours"] = atm  # standalone ATM: these are its own hours
            else:
                item["extras"]["opening_hours:atm"] = atm

        yield item
    
