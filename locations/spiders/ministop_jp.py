from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Sells, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class MinistopJPSpider(CanlySpider):
    name = "ministop_jp"
    api_endpoint = "https://api.site.can-ly.com/v2/directories/94/shops/search"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["openStatus"] != "IS_ALREADY_OPEN":
            return

        if feature["nameKanji"].startswith("ミニストップ"):
            item["branch"] = feature["nameKanji"].removeprefix("ミニストップ").strip()  # "Ministop"
            item["brand"] = "Ministop"
            item["brand_wikidata"] = "Q1038929"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        elif feature["nameKanji"].startswith("MINI SOF"):
            item["branch"] = feature["nameKanji"].removeprefix("MINI SOF").strip()
            item["brand"] = "MINISOF"
            item["brand_wikidata"] = "Q134958024"
            apply_category(Categories.ICE_CREAM, item)
        elif feature["nameKanji"].startswith("cisca"):
            item["branch"] = feature["nameKanji"].removeprefix("cisca").strip()
            item["brand"] = "cisca"
            item["brand_wikidata"] = "Q134958099"
            apply_category(Categories.CAFE, item)
        else:
            self.logger.warning("Unknown brand name as prefix to location name: {}".format(feature["nameKanji"]))

        item["website"] = f"https://map.ministop.co.jp/detail/{feature['storeCode']}/"
        item.pop("name", None)

        yield item

    def post_process_detail(
        self, item: Feature, response: Response, feature: dict, cms_item_values: list
    ) -> Iterable[Feature]:
        """Extract additional attributes from the detail page."""
        for cms_item in cms_item_values:
            content = cms_item.get("content", {})
            keyword = content.get("keyword")

            # Products: alcohol and tobacco
            if keyword == "products":
                for product in content.get("checkBoxComposite", {}).get("items", []):
                    if product.get("checked"):
                        text = product.get("text")
                        if text == "お酒":  # Alcohol
                            apply_yes_no(Sells.ALCOHOL, item, True)
                        elif text == "たばこ":  # Tobacco
                            apply_yes_no(Sells.TOBACCO, item, True)

            # Services: ATM, WiFi, copying, tax-free
            elif keyword == "service":
                for service in content.get("checkBoxComposite", {}).get("items", []):
                    if not service.get("checked"):
                        continue
                    text = service.get("text")
                    if text == "ATM":
                        apply_yes_no(Extras.ATM, item, True)
                    elif text in ("ciscaWiFi", "ソフトバンクWiFi"):
                        apply_yes_no(Extras.WIFI, item, True)
                    elif text in ("コピー", "マルチコピー（シャープ）"):
                        apply_yes_no(Extras.COPYING, item, True)
                    elif text == "Tax-free Shop":
                        apply_yes_no(Extras.DUTY_FREE, item, True)

            # Delivery: Uber Eats, 出前館
            elif keyword == "delivery":
                for delivery in content.get("checkBoxComposite", {}).get("items", []):
                    if delivery.get("checked"):
                        text = delivery.get("text")
                        if text in ("Uber Eats", "出前館"):
                            apply_yes_no(Extras.DELIVERY, item, True)

        yield item
