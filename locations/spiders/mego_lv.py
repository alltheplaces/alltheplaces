from scrapy.http import Response

from locations.json_blob_spider import JSONBlobSpider


class MegoLVSpider(JSONBlobSpider):
    name = "mego_lv"
    start_urls = ["https://mego.lv/wp-admin/admin-ajax.php?action=store_filter"]
    item_attributes = {"brand_wikidata": "Q16363314"}

    def extract_json(self, response: Response) -> list[dict]:
        stores = []
        for stores_data in response.json()["data"].values():
            stores.extend(stores_data["stores"])
        return stores

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("mapLocation", {}))
        feature["name"] = "Mego"
