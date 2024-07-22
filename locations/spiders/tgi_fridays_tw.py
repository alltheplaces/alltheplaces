from scrapy import Spider

from locations.dict_parser import DictParser
from locations.spiders.tgi_fridays_us import TgiFridaysUSSpider


class TgiFridaysTWSpider(Spider):
    name = "tgi_fridays_tw"
    item_attributes = TgiFridaysUSSpider.item_attributes
    start_urls = ["https://www.tgifridays.com.tw/api/v0/data/locations-tgif-tw.json"]
    # custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        resp_json = response.json()
        for language in resp_json:
            if language["code"] == "en-US":
                en_data = language["regions"]
            else:
                zh_data = language["regions"]
        for region_en in en_data:
            for store_en in region_en["locations"]:
                item = DictParser.parse(store_en)
                phone = store_en.get("phone", {})
                item["ref"] = store_en.get("key")
                item["phone"] = phone.get("country") + phone.get("area") + phone.get("number")
                item["extras"]["reservation:website"] = store_en.get("urls", {}).get("reservations")
                item["image"] = store_en.get("photo")
                item["lat"] = store_en.get("map", {}).get("latitude")
                item["lon"] = store_en.get("map", {}).get("longitude")

                # Go into the chinese list and grab the name and address in chinese. (Search by key)
                for region_zh in zh_data:
                    if region_en.get("key") == region_zh.get("key"):
                        for store_zh in region_zh["locations"]:
                            if store_en.get("key") == store_zh.get("key"):
                                item["extras"]["addr:full:zh"] = store_zh.get("address")
                                item["extras"]["name:zh"] = store_zh.get("name")
                yield item
