import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SeimsJPSpider(Spider):
    name = "seims_jp"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in ["w", "x", "z"]:
            yield JsonRequest(url=f"https://store.seims.co.jp/api/point/{points}/")

    def parse(self, response):
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            match store["marker"]["ja"]["name"]:
                case "ドラッグセイムス":
                    item["brand_wikidata"] = "Q11456137"
                case "ドラッグユタカ":
                    item["brand"] = "ドラッグユタカ"  # complicated NSI
                    item["brand_wikidata"] = "Q11345601"
                case "アメリカンドラッグ":
                    item["brand"] = "アメリカンドラッグ"
                    item["brand_wikidata"] = "Q11285057"  # no NSI
                case "オストジャパン":
                    item["brand"] = store["marker"]["ja"]["name"]  # this and others have no Wikidata
                case "スーパードラッグキリン":
                    item["brand"] = store["marker"]["ja"]["name"]
                case "ドラッグストアスマイル":
                    item["brand"] = store["marker"]["ja"]["name"]
                case "救命堂":
                    item["brand"] = store["marker"]["ja"]["name"]
                case _:
                    item["brand"] = store["marker"]["ja"]["name"]

            try:
                item["branch"] = re.search(r"(?:\s)\b\S+$", str(store["name"])).group()
                del item["name"]
            except:
                pass

            item["postcode"] = store["extra_fields"]["郵便番号"]
            item["extras"]["addr:province"] = store["extra_fields"]["都道府県"]
            item["extras"]["branch:ja-Hira"] = store["extra_fields"]["店名かな"]

            if store["extra_fields"]["電話番号"] is not None:
                item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
                if store["extra_fields"]["調剤電話番号"] is not None:
                    item["extras"]["phone:pharmacy"] = f"+81 {store['extra_fields']['調剤電話番号']}"
            else:
                item["phone"] = f"+81 {store['extra_fields']['調剤電話番号']}"

            apply_yes_no("drinking_water:refill", item, store["extra_fields"]["給水器"] == "1")
            apply_yes_no("drive_through", item, store["extra_fields"]["【調剤】調剤ドライブスルー"] == "1")

            apply_yes_no("sells:rice", item, store["extra_fields"]["【取扱】米"] == "1")
            apply_yes_no("sells:meat", item, store["extra_fields"]["【取扱】精肉"] == "1")
            apply_yes_no("sells:pet_supplies", item, store["extra_fields"]["【取扱】ペット用品"] == "1")
            apply_yes_no("sells:dairy", item, store["extra_fields"]["【取扱】乳製品"] == "1")
            apply_yes_no("sells:frozen_food", item, store["extra_fields"]["【取扱】冷凍食品"] == "1")
            apply_yes_no("sells:produce", item, store["extra_fields"]["【取扱】青果"] == "1")
            apply_yes_no("sells:alcohol", item, store["extra_fields"]["【取扱】酒類"] == "1")
            apply_yes_no("sells:contact_lenses", item, store["extra_fields"]["【取扱】コンタクトレンズ"] == "1")
            apply_yes_no("sells:baby_goods", item, store["extra_fields"]["【取扱】ベビー用品"] == "1")

            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, store["extra_fields"]["【支払】ｸﾚｼﾞｯﾄ"] == "1")
            apply_yes_no(PaymentMethods.CONTACTLESS, item, store["extra_fields"]["【支払】ｸﾚｼﾞｯﾄ(タッチ決済)"] == "1")

            if str("".join(filter(str.isdigit, str(store["extra_fields"]["駐車場台数"])))) in ("", "0"):
                pass
            else:
                item["extras"]["parking:capacity:standard"] = str(
                    "".join(filter(str.isdigit, str(store["extra_fields"]["駐車場台数"])))
                )

            item["website"] = f"https://store.seims.co.jp/map/{store['key']}/"
            item["extras"]["website:booking"] = store["extra_fields"]["【調剤】処方せんネット受付URL"]
            item["ref"] = store["key"]
            if store["extra_fields"]["ドラッグストア"] == "1":
                apply_category(Categories.SHOP_CHEMIST, item)
            if store["extra_fields"]["処方せん受付店舗"] == "1":
                apply_category(Categories.PHARMACY, item)
                item["extras"]["dispensing"] = "yes"

            yield item
