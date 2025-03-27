from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiTWSpider(JSONBlobSpider):
    name = "mitsubishi_tw"
    allowed_domains = ["www.mitsubishi-motors.com.tw"]
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }

    def start_requests(self):
        for node_type in ["1", "2"]:
            yield FormRequest(
                url="https://www.mitsubishi-motors.com.tw/do/locationsdo.php",
                formdata={"surl": f"https://api.5230.com.tw/cmcAPI/index.php/getNodeList/index/nodeType/{node_type}"},
                meta={"type": node_type},
            )

    def post_process_item(self, item, response, feature):
        item["ref"] = feature.get("sr_cd")
        item["name"] = feature.get("fullname")
        if response.meta["type"] == "1":
            apply_category(Categories.SHOP_CAR, item)
        elif response.meta["type"] == "2":
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
