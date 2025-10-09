from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SabaSpider(JSONBlobSpider):
    name = "saba"
    item_attributes = {
        "brand": "Saba",
        "brand_wikidata": "Q67808022",
    }
    start_urls = ["https://www.sabaparking.co.uk/o/sabine/v1.0/countries/GB/languages/EN/parkings-clusters"]
    locations_key = "parkingClusterData"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["parkingId"]
        item["name"] = feature["parkingName"]
        item["street"] = feature["parkingAddress"]
        item["city"] = feature["parkingCity"]
        if friendlyUrl := feature.get("friendlyUrl"):
            item["website"] = f"https://www.sabaparking.co.uk/en{friendlyUrl}"

        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, feature["paymentByAMEX"], True)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, feature["paymentByMastercard"], True)
        apply_yes_no(PaymentMethods.VISA, item, feature["paymentByVisa"], True)

        apply_category(Categories.PARKING, item)

        yield item
