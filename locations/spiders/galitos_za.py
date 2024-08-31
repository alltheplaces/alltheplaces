from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class GalitosZASpider(JSONBlobSpider):
    name = "galitos_za"
    item_attributes = {"brand": "Galito's", "brand_wikidata": "Q116619555"}
    start_urls = ["https://admin.goreview.co.za/website/api/locations/search"]
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        data_raw = {
            "domain": "localpages.galitos.co.za",
            "latitude": "null",
            "longitude": "null",
            "attributes": "false",
            "radius": "null",
            "initialLoad": "true",
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data_raw)

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["website"] = location["local_page_url"]
        if item.get("attributes") is not None:
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in item.get("attributes"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-through" in item.get("attributes"))
            apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in item.get("attributes"))
            # Not handled: "Can Trade Off Power Grid", "Dine-in", "Kerbside pickup"
        yield item
