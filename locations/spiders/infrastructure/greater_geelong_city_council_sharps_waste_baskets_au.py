from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class GreaterGeelongCityCouncilSharpsWasteBasketsAUSpider(OpendatasoftExploreSpider):
    name = "greater_geelong_city_council_sharps_waste_baskets_au"
    item_attributes = {"operator": "Greater Geelong City Council", "operator_wikidata": "Q112919122", "nsi_id": "N/A"}
    api_endpoint = "https://www.geelongdataexchange.com.au/api/explore/v2.1/"
    dataset_id = "syringe-bin-locations-city-of-greater-geelong"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.SHARPS_WASTE_BASKET, item)

        if volume_str := feature.get("size"):
            # "volume" is a made-up key that doesn't currently exist in OSM.
            # No other existing key for the volume of a bin appears to
            # currently exist in OSM.
            item["extras"]["volume"] = volume_str

        yield item
