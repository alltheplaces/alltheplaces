from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CuttersSpider(JSONBlobSpider):
    name = "cutters"
    item_attributes = {"brand": "Cutters", "brand_wikidata": "Q106940660"}
    start_urls = ["https://cutters.no/api/salons"]
    locations_key = "salons"

    def pre_process_data(self, salon: dict) -> None:
        salon["street-address"] = salon.pop("address")
        salon["city"] = salon.pop("postalPlace")
        if coordinates := salon.get("coordinates"):
            salon["lat"] = coordinates.get("latitude")
            salon["lon"] = coordinates.get("longitude")

    def post_process_item(self, item: Feature, response: Response, salon: dict, **kwargs):
        if not salon.get("active"):
            return

        item["branch"] = item.pop("name")
        item["extras"]["start_date"] = salon["openingDate"]

        if relativeLocation := salon.get("relativeLocation"):
            item["extras"]["description"] = relativeLocation
        if paymentProviders := salon.get("webPaymentProviders"):
            apply_yes_no(PaymentMethods.VIPPS, item, "vipps" in paymentProviders)

        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item
