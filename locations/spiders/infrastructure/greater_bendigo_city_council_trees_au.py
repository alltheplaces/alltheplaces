import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.vector_file_spider import VectorFileSpider


class GreaterBendigoCityCouncilTreesAUSpider(VectorFileSpider):
    name = "greater_bendigo_city_council_trees_au"
    item_attributes = {"operator": "Greater Bendigo City Council", "operator_wikidata": "Q134285890", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = [
        "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Tree_Planting_2026.fgb",  # 2026
        "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Tree_Planting_2025.fgb",  # 2025
        "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Tree_Planting_2024.fgb",  # 2024
        "https://connect.pozi.com/userdata/bendigo-publisher/Pozi_Public_City_of_Greater_Bendigo/Trees.fgb",  # Pre 2024
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["AssetID"])
        apply_category(Categories.NATURAL_TREE, item)
        if house_number := feature.get("House_Number"):
            item["housenumber"] = house_number
        if street_name := feature.get("Street_Name"):
            item["street"] = street_name
        if suburb := feature.get("Suburb"):
            item["city"] = suburb
        if planting_year := feature.get("Planting_Year"):
            item["extras"]["start_date"] = str(planting_year)

        if asset_type := feature.get("Asset Type"):
            # Pre 2024 dataset format
            taxon_cn = asset_type
            cultivar = None
        elif species_raw := feature.get("Species"):
            # 2024-2026 dataset format
            taxon_cn = species_raw
            if cultivar_raw := feature.get("Cultivar"):
                cultivar = cultivar_raw
        else:
            return

        if m := re.match(r"^([\w ]+) - ([\w ]+)", taxon_cn):
            if cultivar and cultivar != "Not Specified":
                item["extras"]["species"] = re.sub(r"\s+", " ", m.group(1) + f" '{cultivar}'").strip()
                item["extras"]["taxon:en"] = re.sub(r"\s+", " ", m.group(2) + f" '{cultivar}'").strip()
            else:
                item["extras"]["species"] = re.sub(r"\s+", " ", m.group(1)).strip()
                item["extras"]["taxon:en"] = re.sub(r"\s+", " ", m.group(2)).strip()
        elif taxon_cn == "Not Specified":
            pass
        else:
            if cultivar and cultivar != "Not Specified":
                item["extras"]["species"] = re.sub(r"\s+", " ", taxon_cn + f" '{cultivar}'").strip()
            else:
                item["extras"]["species"] = re.sub(r"\s+", " ", taxon_cn).strip()

        yield item
