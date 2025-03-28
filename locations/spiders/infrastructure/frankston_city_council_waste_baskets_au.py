import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class FrankstonCityCouncilWasteBasketsAUSpider(OpendatasoftExploreSpider):
    name = "frankston_city_council_waste_baskets_au"
    item_attributes = {"operator": "Frankston City Council", "operator_wikidata": "Q132472668", "nsi_id": "N/A"}
    api_endpoint = "https://data.frankston.vic.gov.au/api/explore/v2.1/"
    dataset_id = "frankston-city-public-bins"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["housenumber"] = feature.get("house")
        item["street"] = feature.get("road")
        item["state"] = "VIC"
        apply_category(Categories.WASTE_BASKET, item)

        if volume_str := feature.get("binsize"):
            volume_str = volume_str.replace("M", "000")  # m^3 to Litres
            if m := re.search(r"(\d+)", volume_str):
                volume_int = int(m.group(1))
                # "volume" is a made-up key that doesn't currently exist in OSM.
                # No other existing key for the volume of a bin appears to
                # currently exist in OSM.
                item["extras"]["volume"] = f"{volume_int} Litres"

        if waste_type := feature.get("bintype"):
            match waste_type:
                case "DWB" | "DWB Dispenser":
                    item["extras"]["waste"] = "dog_excrement"
                case "Recycling" | "Recycle":
                    item["extras"]["waste"] = "recycling"
                case "Waste":
                    item["extras"]["waste"] = "trash"
                case _:
                    self.logger.warning("Unknown waste type: {}".format(waste_type))

        yield item
