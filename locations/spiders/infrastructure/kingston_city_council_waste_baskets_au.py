import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KingstonCityCouncilWasteBasketsAUSpider(JSONBlobSpider):
    name = "kingston_city_council_waste_baskets_au"
    item_attributes = {"operator": "Kingston City Council", "operator_wikidata": "Q56477816", "state": "VIC"}
    allowed_domains = ["data.gov.au"]
    start_urls = [
        "https://data.gov.au/data/dataset/7d041990-5658-43b2-8f60-1dcc280de87c/resource/ebe81e8f-f014-4ba7-8eba-e9818b3ef493/download/kingston-city-council-public-bins.json"
    ]
    locations_key = "features"
    no_refs = True

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if m := re.search(r"(\d+) Bins? Landfill", feature["ToolTip"]):
            landfill_count = int(m.group(1))
            for landfill_bin_no in range(0, landfill_count):
                landfill_bin = item.deepcopy()
                apply_category(Categories.WASTE_BASKET, landfill_bin)
                yield landfill_bin
        if m := re.search(r"(\d+) Bins? Recycling", feature["ToolTip"]):
            recycling_count = int(m.group(1))
            for recycling_bin_no in range(0, recycling_count):
                recycling_bin = item.deepcopy()
                apply_category(Categories.RECYCLING, recycling_bin)
                yield recycling_bin
