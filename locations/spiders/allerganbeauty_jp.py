from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class AllerganbeautyJPSpider(Spider):
    name = "allerganbeauty_jp"

    start_urls = ["https://clinics.allerganbeauty.jp/api/all_point"]
    allowed_domains = ["clinics.allerganbeauty.jp"]
    country_code = "JP"

    TYPES = {
        "皮": "dermatology",
        "アレルギー": "allergology",
        "婦人": "gynaecology",
        "形成": "plastic_surgery",
        "泌尿": "urology",
        "内科": "internal",
        "眼科": "ophthalmology",
        "麻酔": "anaesthetics",
        "耳鼻咽喉": "otolaryngology",
        "口膣外科": "stomatology",
        "漢方": "traditional_chinese_medicine",
        "リウマチ": "rheumatology",
        "消化器": "gastroenterology",
        "小児": "paediatrics",
        "リハビリテーション": "physiatry",
        "腎臓": "nephrology",
        "人間ドック": "general",
        "美容歯": "implantology",
        "肛門": "proctology",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["shop_list"]:

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = store.get("施設URL")
            item["phone"] = f"+81 {store.get('tel')}"

            apply_category(Categories.CLINIC, item)
            speciality = []
            for jaspec, enspec in self.TYPES.items():
                try:
                    if jaspec in store.get("診療科目"):
                        speciality.append(enspec)
                except TypeError:
                    pass
            if speciality:
                if len(speciality) == 1:
                    item["extras"]["healthcare:speciality"] = speciality[0]
                else:
                    item["extras"]["healthcare:speciality"] = ";".join(speciality)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, store["クレジットカード利用可"] == "1")
            if store["完全予約制"] == 1:
                apply_category({"reservation": "required"}, item)
            if store["女性限定"] == 1:
                apply_category({"female": "yes"}, item)
            if store["駐車場あり"] == 1:
                apply_category({"parking": "yes"}, item)
            if store["オンライン予約可"] == 1:
                item["extras"]["website:booking"] = store["予約URL"]

            yield item
