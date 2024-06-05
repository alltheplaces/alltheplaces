from typing import Iterable

from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class ClairesSpider(RioSeoSpider):
    name = "claires"
    item_attributes = {"brand_wikidata": "Q2974996"}
    end_point = "https://maps.stores.claires.com/api/"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature["branch"] = feature.pop("name")

        yield feature
