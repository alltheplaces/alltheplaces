from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class SunAutoServiceUSSpider(RioSeoSpider):
    name = "sun_auto_service_us"
    item_attributes = {"brand": "Sun Auto Service", "brand_wikidata": "Q118383798"}
    end_point = "https://maps.locations.sun.auto.prod.rioseo.com"
    template = "search"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature["branch"] = location["location_display_name"].removeprefix("{} ".format(location["location_name"]))
        feature["website"] = feature["website"].replace("https://locations.sun.auto.prod.rioseo.com/", "https://locations.sun.auto.prod.rioseo.com/sunauto/")
        yield feature
