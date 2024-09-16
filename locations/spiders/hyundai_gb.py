from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiGBSpider(JSONBlobSpider):
    name = "hyundai_gb"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/uk/en/retailer-locator.html"]

    def extract_json(self, response: Response) -> list:
        js_blob = response.xpath('//div[@data-js-module="dealer-locator"]/@data-js-content').get()
        json_dict = loads(js_blob)
        return json_dict["dealers"]["gb"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("fullDealerName")
        item["street_address"] = clean_address([feature.get("addressLine1"), feature.get("addressLine2")])
        item["website"] = feature.get("webSite")
        item["opening_hours"] = OpeningHours()
        for day_abbrev in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sa", "Su"]:
            item["opening_hours"].add_range(
                DAYS_EN[day_abbrev], *feature.get(f"openingHours{day_abbrev}", "").split("-", 1), "%H:%M"
            )

        services = feature["dealerProperties"][0].get("services")
        for service in services:
            if service["serviceId"] == "sales":
                sales_feature = item.copy()
                sales_feature["ref"] = sales_feature["ref"] + "_Sales"
                apply_category(Categories.SHOP_CAR, sales_feature)
                yield sales_feature
            elif service["serviceId"] == "service":
                service_feature = item.copy()
                service_feature["ref"] = service_feature["ref"] + "_Service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_feature)
                yield service_feature
            elif service["serviceId"] == "certified-used-car-program" or service["serviceId"] == "HyundaiPromiseApprovedUsedCars":
                continue
            elif service["serviceId"] == "hyundai-business-centre":
                continue
            elif service["serviceId"] == "dealership-nexo":
                continue
            else:
                raise ValueError("Unknown feature type: {} ({})".format(service["serviceTitle"], service["serviceId"]))
