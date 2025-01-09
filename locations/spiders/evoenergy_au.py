import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class EvoenergyAUSpider(RosettaAPRSpider):
    name = "evoenergy_au"
    item_attributes = {"operator": "Evoenergy", "operator_wikidata": "Q111081969"}
    start_urls = ["https://apr.evoenergy.com.au/"]
    data_files = [
        RosettaAPRDataFile(url="https://content.rosettaanalytics.com.au/evoenergy_layers_serve_2024/Evoenergy_Zone_Substations.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_zone_substations"),
        RosettaAPRDataFile(url="https://content.rosettaanalytics.com.au/evoenergy_layers_serve_2024/Evoenergy_Switching_Stations.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_switching_stations"),
    ]

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./evoenergy_data/Evoenergy_Zone_Substations_Technical_Specifications.csv", file_type="csv", encrypted=True, callback_function_name="parse_zone_substation_attribs", column_headings=["name", "comissioned_date", "voltages", "total_capacity", "firm_capacity", "transformers_count"])
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_ZONE, properties)
            new_ref = properties["ref"].removesuffix(" Zone Substation")
            if new_ref in features_dict.keys():
                if voltages_str := features_dict[new_ref]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if total_capacity := features_dict[new_ref]["total_capacity"]:
                    properties["extras"]["rating"] = total_capacity
            items.append(Feature(**properties))
        return items

    def parse_switching_stations(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            items.append(Feature(**properties))
        return items
