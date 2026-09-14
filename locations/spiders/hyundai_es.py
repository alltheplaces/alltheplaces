from json import loads
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.hyundai_gb import HyundaiGBSpider


class HyundaiESSpider(HyundaiGBSpider):
    name = "hyundai_es"
    allowed_domains = ["www.hyundai.com"]
    start_urls = ["https://www.hyundai.com/es/es/concesionarios.html"]

    def extract_json(self, response: Response) -> list:
        js_blob = response.xpath('//div[@data-js-module="dealer-locator"]/@data-js-content').get()
        json_dict = loads(js_blob)
        return json_dict["dealers"]["es"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Spanish dealer records use their own localised serviceId vocabulary
        # ("Nuevos"/"Seminuevos"/"Taller") rather than the English serviceId
        # strings used by other Hyundai markets, so this overrides (rather
        # than reuses) HyundaiGBSpider.post_process_item's service handling.
        item["branch"] = feature.get("fullDealerName")
        item["street_address"] = clean_address([feature.get("addressLine1"), feature.get("addressLine2")])
        item["website"] = feature.get("webSite")
        item["opening_hours"] = self.parse_opening_hours(feature)

        if not item["ref"]:
            # A small number of records have an empty "id", so fall back to
            # the (also unique) internal "localId" field.
            item["ref"] = feature.get("localId")

        service_ids = set()
        for dealer_property in feature.get("dealerProperties", []):
            for service in dealer_property.get("services", []):
                service_ids.add(service["serviceId"])

        if "Nuevos" in service_ids or "Seminuevos" in service_ids:
            sales_feature = item.deepcopy()
            sales_feature["ref"] = item["ref"] + "_Sales"
            apply_category(Categories.SHOP_CAR, sales_feature)
            yield sales_feature

        if "Taller" in service_ids or "service" in service_ids:
            service_feature = item.deepcopy()
            service_feature["ref"] = item["ref"] + "_Service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_feature)
            yield service_feature
