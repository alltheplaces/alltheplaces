import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, Sells, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST


class MatsukiyoJPSpider(Spider):
    name = "matsukiyo_jp"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ja",
            "Connection": "keep-alive",
            "Referer": "https://www.matsukiyococokara-online.com/map/search",
            "user-agent": FIREFOX_LATEST,
        }
    }
    start_urls = ["https://www.matsukiyococokara-online.com/map/s3/json/stores.json"]
    allowed_domains = ["www.matsukiyococokara-online.com"]
    requires_proxy = True
    country_code = "JP"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():

            item = DictParser.parse(store)

            match store["icon"]:
                case 1:
                    item.update({"brand": "マツモトキヨシ", "brand_wikidata": "Q8014776"})
                case 3:
                    item.update({"brand": "matsukiyoLAB", "brand_wikidata": "Q8014776"})
                case 4:
                    item.update({"brand": "ファミリードラッグ"})
                case 9:
                    item.update({"brand": "petit madoca"})
                case 12:
                    item.update({"brand": "くすりのラブ", "brand_wikidata": "Q11347308"})
                case 14:
                    item.update({"brand": "シメノドラッグ", "brand_wikidata": "Q11588146"})
                case 15:
                    item.update({"brand": "ダルマ", "brand_wikidata": "Q11317431"})
                case 16:
                    item.update({"brand": "ぱぱす", "brand_wikidata": "Q11276061"})
                case 17:
                    item.update({"brand": "ヘルスバンク", "brand_wikidata": "Q11522264"})
                case 18:
                    item.update({"brand": "ミドリ薬品"})
                case 19:
                    item.update({"brand": "ココカラファイン", "brand_wikidata": "Q11301948"})
                case 30:
                    item.update({"brand": "ココカラファイン", "brand_wikidata": "Q11301948"})
                case 31:
                    item.update({"brand": "セイジョー", "brand_wikidata": "Q11314133"})
                case 32:
                    item.update({"brand": "ドラッグセガミ", "brand_wikidata": "Q11301949"})
                case 33:
                    item.update({"brand": "ジップドラッグ", "brand_wikidata": "Q11309539"})
                case 34:
                    item.update({"brand": "ライフォート", "brand_wikidata": "Q11346469"})
                case 35:
                    item.update({"brand": "クスリのコダマ", "brand_wikidata": "Q11302198"})
                case 36:
                    item.update({"brand": "ココカラファインイズミヤ"})
                case 37:
                    item.update({"brand": "クスリ岩崎チェーン"})

            if store["businesshours"][2] == "1":
                item["opening_hours"] = "24/7"

            if store["services"][4] == "1":
                apply_category(Categories.PHARMACY, item)
                item["extras"]["dispensing"] = "yes"
            else:
                apply_category(Categories.SHOP_CHEMIST, item)
                item["extras"]["dispensing"] = "no"

            apply_yes_no("sells:baby_goods", item, store["products"][12] == "1")
            apply_yes_no(Sells.PET_SUPPLIES, item, store["products"][13] == "1")
            if store["products"][14] == "1":
                item["extras"]["medical_supply"] = "home_care"
            apply_yes_no("sells:sweets", item, store["products"][15] == "1")
            apply_yes_no("sells:food", item, store["products"][16] == "1")
            apply_yes_no("sells:rice", item, store["products"][17] == "1")
            apply_yes_no("sells:alcohol", item, store["products"][18] == "1")
            apply_yes_no(Sells.TOBACCO, item, store["products"][19] == "1")

            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, store["payments"][0] == "1")
            apply_yes_no(PaymentMethods.EDY, item, store["payments"][1] == "1")
            apply_yes_no(PaymentMethods.ID, item, store["payments"][2] == "1")
            apply_yes_no(PaymentMethods.QUICPAY, item, store["payments"][3] == "1")
            apply_yes_no(PaymentMethods.APPLE_PAY, item, store["payments"][4] == "1")
            apply_yes_no("payment:icsf", item, store["payments"][5] == "1")
            apply_yes_no("payment:icoca", item, store["payments"][6] == "1")
            apply_yes_no(PaymentMethods.UNIONPAY, item, store["payments"][7] == "1")
            apply_yes_no(PaymentMethods.ALIPAY, item, store["payments"][8] == "1")
            apply_yes_no(PaymentMethods.WECHAT, item, store["payments"][9] == "1")
            apply_yes_no(PaymentMethods.D_BARAI, item, store["payments"][10] == "1")
            apply_yes_no("payment:au_pay", item, store["payments"][11] == "1")
            apply_yes_no(PaymentMethods.WAON, item, store["payments"][12] == "1")
            apply_yes_no(PaymentMethods.PAYPAY, item, store["payments"][13] == "1")
            apply_yes_no(PaymentMethods.MERPAY, item, store["payments"][14] == "1")
            apply_yes_no(PaymentMethods.RAKUTEN_PAY, item, store["payments"][15] == "1")
            apply_yes_no("payment:quo_pay", item, store["payments"][16] == "1")

            item["website"] = f"https://www.matsukiyococokara-online.com/map?kid={store['id']}"

            item["phone"] = f"+81 {store['phone_store']}"
            if store["phone_dispensing"] is not None:
                item["extras"]["phone:pharmacy"] = f"+81 {store['phone_dispensing']}"
            if store["fax_dispensing"] is not None:
                item["extras"]["fax"] = f"+81 {store['fax_dispensing']}"

            if str("".join(filter(str.isdigit, str(store["parking_count"])))) in ("", "0"):
                pass
            elif "共用" in str(store["parking_count"]):
                item["extras"]["parking"] = "yes"
            else:
                item["extras"]["parking:capacity:standard"] = str(
                    "".join(filter(str.isdigit, str(store["parking_count"])))
                )

            try:
                item["branch"] = re.search(r"(?:\s)\b\S+$", str(store["name"])).group()
                del item["name"]
            except:
                pass

            item["extras"]["start_date"] = re.search(r"^\S*", str(store["publish_start"])).group()

            yield item
