from locations.json_blob_spider import JSONBlobSpider


class DesaTRSpider(JSONBlobSpider):
    name = "desa_tr"
    item_attributes = {
        "brand": "Desa",
        "brand_wikidata": "Q17513880",
    }
    start_urls = ["https://www.desa.com.tr/stores/?format=json&country=1"]

    def extract_json(self, response):
        return response.json()["results"]

    def post_process_item(self, item, response, location):
        # {"pk": 679,
        # "name": "DESA / SAMSONITE  Çorlu Orion",
        # "township": {"pk": 876, "is_active": True, "name": "ÇORLU", "city": {"pk": 73, "is_active": True, "name": "TEKİRDAĞ", "country": {"pk": 1, "is_active": True, "name": "TÜRKİYE", "code": "tr", "translations": None}}},
        # "district": None, "address": "Omurtak Cad. Muhittin Mah. Mağaza No:9",
        # "phone_number": "0282 673 53 14",
        # "fax_phone_number": None, "image": None,
        # "store_hours": [],
        # "latitude": "41.15190400", "longitude": "27.83437700",
        # "is_active": True, "click_and_collect": False, "store_type": None, "kapida_enabled": False, "fast_delivery": False, "config": {"districts": [], "price_list_id": None, "quota": None, "stock_list_id": None}, "group": None, "sort_order": None, "erp_code": "121-1", "translations": None, "related_retail_stores": [], "absolute_url": "/address/retail_store/679/"}}
        item["ref"] = location["pk"]
        item["city"] = location["township"]["city"]["name"]  # TODO: What is township name vs this?
        item["street_address"] = item.pop("addr_full")
        yield item
