from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CopenhagenMunicipalityPlaygroundsDKSpider(JSONBlobSpider):
    name = "copenhagen_municipality_playgrounds_dk"
    item_attributes = {"operator": "Københavns Kommune", "operator_wikidata": "Q504125", "nsi_id": "N/A"}
    allowed_domains = ["wfs-kbhkort.kk.dk"]
    start_urls = [
        "https://wfs-kbhkort.kk.dk/k101/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=k101:legeplads&outputFormat=json&SRSNAME=EPSG:4326"
    ]
    locations_key = "features"
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["legeplads_id"])
        item["name"] = feature["navn"]
        item["street_address"] = feature["adressebeskrivelse"]
        item["city"] = feature["bydel"]
        apply_category(Categories.LEISURE_PLAYGROUND, item)
        yield item
