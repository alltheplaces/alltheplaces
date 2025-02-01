from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BanyuleCityCouncilAUSpider(JSONBlobSpider):
    name = "banyule_city_council_au"
    item_attributes = {"operator": "Banyule City Council", "operator_wikidata": "Q56477775"}
    allowed_domains = ["www.banyule.vic.gov.au"]
    start_urls = ["https://www.banyule.vic.gov.au/ocmaps/layer"]
    locations_key = ["layerItems"]

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {
            "Bounds": "-90,-180,90,180",
            "IdList": [
                "7188d470-e264-4b01-8a85-e5c468e95a7f",
                "62e6b994-4054-4030-a3b8-b8865618d715",
                "244598c4-2d5c-4646-8776-cb6c95c9a69c",
                "03a4b1b1-a7e0-4bde-b83a-5b4768c96b61",
                "f1cdc1d3-5041-4db3-acd8-425d65ef8256",
                "c5583c9d-15b5-419a-a7a6-fae3c406cfc4",  #Libraries
                "8e840aad-2f8b-4426-8f75-401d44fec283",  #MCH
                "57e35761-680e-48ef-ad0e-8355a7e5f9c9",  #Preschools
            ],
            "LanguageCode": "en-AU",
            "MapId": "8b0f367d-0765-4ea7-8398-47ea239c9a95",
            "RefreshResults": True,
            "UniqueId": None
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["ContentId"]
        item["name"] = feature["ContentTitle"]
        match feature["Name"]:
            case "Bike repair station":
                apply_category(Categories.BICYCLE_REPAIR_STATION, item)
            case "Dog-friendly parks (fenced)":
                apply_category(Categories.LEISURE_DOG_PARK, item)
            case "Kindergartens":
                apply_category(Categories.KINDERGARTEN, item)
            case "Leisure centre":
                apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            case "Library":
                apply_category(Categories.LIBRARY, item)
            case "Maternal and Child Health centre":
                apply_category(Categories.NURSE_CLINIC, item)
            case "Neighbourhood houses":
                apply_category(Categories.COMMUNITY_CENTRE, item)
            case "Parks":
                apply_category(Categories.LEISURE_PARK, item)
            case _:
                raise ValueError("Unknown feature type: {}".format(feature["Name"]))
        yield item
