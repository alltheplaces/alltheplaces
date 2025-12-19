from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ElinoilGRSpider(JSONBlobSpider):
    name = "elinoil_gr"
    item_attributes = {"brand": "ΕΛΙΝΟΙΛ", "brand_wikidata": "Q12876543"}
    start_urls = ["https://elin.gr/backoffice/MapMarkers/GetMapMarkers?language=en"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FUEL_STATION, item)
        services = feature.get("Services")
        apply_yes_no(Extras.TOILETS, item, "WC" in services)
        apply_yes_no(Fuel.DIESEL, item, "Diesel Crystal Next" in services)
        apply_yes_no(Fuel.LPG, item, "Gas Υγραέριο" in services)
        apply_yes_no(PaymentMethods.DINERS_CLUB, item, "Diners Club International" in services)
        yield item
