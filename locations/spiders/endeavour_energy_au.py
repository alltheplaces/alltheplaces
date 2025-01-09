import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class EndeavourEnergyAUSpider(RosettaAPRSpider):
    name = "endeavour_energy_au"
    item_attributes = {"operator": "Endeavour Energy", "operator_wikidata": "Q5375986"}
    start_urls = ["https://dapr.endeavourenergy.com.au/"]
    data_files = [
        RosettaAPRDataFile(url="./layers/Zone-Substations_Endeavour.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_zone_substations"),
        RosettaAPRDataFile(url="./layers/Transmission_Sub_Station_Endeavour.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_transmission_substations"),
        RosettaAPRDataFile(url="./layers/Supply_Point_Station_Endeavour.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_bulk_supply_points"),
    ]

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            if feature["Name"].upper().endswith("(PROPOSED)"):
                continue
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./endeavour_data/Zone_Substation_Data_Technical_Endeavour.csv", file_type="csv", encrypted=True, callback_function_name="parse_zone_substation_attribs", column_headings=["name", "voltages", "transformers", "installed_capacity_mva", "secure_capacity_mva", "peak_load_exceeded_hours", "embedded_generation_mw"])
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_ZONE, properties)
            if properties["ref"] in features_dict.keys():
                if voltages_str := features_dict[properties["ref"]]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if installed_capacity_mva := features_dict[properties["ref"]]["installed_capacity_mva"]:
                    properties["extras"]["rating"] = str(installed_capacity_mva) + " MVA"
            items.append(Feature(**properties))
        return items

    def parse_transmission_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["Name"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./endeavour_data/Transmission_Sub_Station_Technical_Endeavour.csv", file_type="csv", encrypted=True, callback_function_name="parse_transmission_substation_attribs", column_headings=["name", "voltages", "transformers", "installed_capacity_mva", "secure_capacity_mva", "peak_load_exceeded_hours", "embedded_generation_mw"])
        return (items, next_data_file)

    def parse_transmission_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            if properties["ref"] in features_dict.keys():
                if voltages_str := features_dict[properties["ref"]]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if installed_capacity_mva := features_dict[properties["ref"]]["installed_capacity_mva"]:
                    properties["extras"]["rating"] = str(installed_capacity_mva) + " MVA"
            items.append(Feature(**properties))
        return items

    def parse_bulk_supply_points(self, features: list[dict]) -> list[Feature]:
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
