import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


def decode_phones(data_item: dict) -> list[str]:
    phones = []
    no_store_number = "ไม่มีเบอร์ร้าน"
    for key in ["mobile", "tel"]:
        if key in data_item and data_item[key] and data_item[key] != no_store_number and data_item[key] != "N/A":
            phone_entries = re.split(r"[ ,]", data_item[key])
            phones.append(phone_entries[0].strip())
    return phones


class BigCTHSpider(scrapy.Spider):
    name = "big_c_th"
    item_attributes = {"brand": "Big C", "brand_wikidata": "Q858665"}
    start_urls = ["https://corporate.bigc.co.th/include/get_store.php"]

    def parse(self, response, **kwargs):
        for data_item in response.json():
            shop_id = data_item["id_shop_type"]
            item = DictParser.parse(data_item)
            item["lat"] = item["lat"].replace(",", "").replace(" ", "")
            item["lon"] = item["lon"].replace(",", "").replace(" ", "")
            item["ref"] = data_item["store_no"]
            item["name"] = item["extras"]["name:th"] = data_item["name_th"]
            item["extras"]["name:en"] = data_item["name_en"]
            item["addr_full"] = item["extras"]["addr:full:th"] = data_item["address_th"]
            item["extras"]["addr:full:en"] = data_item["address_en"]
            item["website"] = item["extras"]["website:th"] = (
                "https://corporate.bigc.co.th/find-a-store?branch={}&lang=th".format(item["ref"])
            )
            item["extras"]["website:en"] = "https://corporate.bigc.co.th/find-a-store?branch={}&lang=en".format(
                item["ref"]
            )
            item["extras"]["check_date"] = data_item["update_date"] or data_item["create_date"]
            phones = decode_phones(data_item)

            item["phone"] = "; ".join(phones)

            if shop_id == "5":
                item["brand"] = "Big C Mini"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif shop_id == "6":
                item["brand"] = "Pure Pharmacy"
                item["brand_wikidata"] = "Q125936488"
                apply_category(Categories.PHARMACY, item)
            elif shop_id == "7":  # Depot
                continue
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
