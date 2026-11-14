from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Sells, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class CainzJPSpider(CanlySpider):
    name = "cainz_jp"
    item_attributes = {"brand": "カインズホーム", "brand_wikidata": "Q11293852"}
    brand_key = "411"

    ATTRIBUTES = {
        "多目的トイレ": Extras.TOILETS_WHEELCHAIR,
        "フリーWi-Fi": Extras.WIFI,
        "ペットと一緒に入店可": Extras.PETS_ALLOWED,
        "ATM": Extras.ATM,
        "授乳室": Extras.BABY_FEEDING_ROOM,
        "工具レンタル": Extras.RENTAL,
        "カインズリカー（酒）": Sells.ALCOHOL,
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["businessStatus"] != "OPEN":
            return

        # カインズリフォーム are renovation consultation desks, not shops.
        if feature["nameKanji"].startswith("カインズリフォーム"):
            return

        item["branch"] = feature["nameKanji"].removeprefix("カインズ").strip()
        item["website"] = f"https://map.cainz.com/detail/{feature['storeCode']}/"
        apply_category(Categories.SHOP_DOITYOURSELF, item)

        yield item

    def post_process_detail(
        self, item: Feature, response: Response, feature: dict, cms_item_values: list
    ) -> Iterable[Feature]:
        for component in cms_item_values:
            content = component["content"]
            if content["componentName"] == "checkBoxOnOffLabel":
                for facility in content["checkBoxOnOffLabel"]["items"]:
                    if attribute := self.ATTRIBUTES.get(facility["label"]):
                        apply_yes_no(attribute, item, facility["checked"])
            elif content["componentName"] == "checkBoxIconTextWithUrl":
                for offering in content["checkBoxIconTextWithUrl"]["items"]:
                    if not offering["checked"]:
                        continue
                    if offering["label"].startswith("ドラッグコーナー"):
                        apply_yes_no(Sells.MEDICINE, item, True)
                    elif attribute := self.ATTRIBUTES.get(offering["label"]):
                        apply_yes_no(attribute, item, True)

        yield item
