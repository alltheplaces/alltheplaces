from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class FrankstonCityCouncilFacilitiesAUSpider(OpendatasoftExploreSpider):
    name = "frankston_city_council_facilities_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "nsi_id": "N/A"}
    api_endpoint = "https://data.frankston.vic.gov.au/api/explore/v2.1/"
    dataset_id = "frankston-city-council-facilities"
    no_refs = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["state"] = "VIC"
        item["phone"] = feature.get("contact_ph")
        match feature["type"]:
            case "Aquatic Centre":
                apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
                item["extras"]["access"] = "yes"
                item["extras"]["sport"] = "swimming"
            case "Library" | "Toy Library":
                apply_category(Categories.LIBRARY, item)
                item["extras"]["access"] = "yes"
            case "Maternal and Child Health":
                apply_category(Categories.NURSE_CLINIC, item)
            case "Public WiFi":
                apply_category(Categories.ANTENNA, item)
                item["extras"]["internet_access"] = "wlan"
                item["extras"]["internet_access:fee"] = "no"
                item["extras"]["internet_access:operator"] = self.item_attributes["operator"]
                item["extras"]["internet_access:operator:wikidata"] = self.item_attributes["operator_wikidata"]
            case _:
                return
        yield item
