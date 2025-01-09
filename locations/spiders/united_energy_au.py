import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class UnitedEnergyAUSpider(RosettaAPRSpider):
    name = "united_energy_au"
    item_attributes = {"operator": "United Energy", "operator_wikidata": "Q48790747"}
    start_urls = ["https://dapr.unitedenergy.com.au/"]
    data_files = [
        RosettaAPRDataFile(url="https://content.rosettaanalytics.com.au/united_energy_layers_serve2/United_Energy_Zone_Substations.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_zone_substations"),
        RosettaAPRDataFile(url="https://content.rosettaanalytics.com.au/united_energy_layers_serve2/United_Energy_Distribution_Substations.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_transformers"),
    ]

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"].upper().split(" ZONE SUBSTATION", 1)[0].split(" TERMINAL STATION", 1)[0],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./ue_data/ue_tech_spec_zs.csv", file_type="csv", encrypted=True, callback_function_name="parse_zone_substation_attribs", column_headings=["name", "voltages", "capacity_mva", "unknown1", "unknown2", "unknown3", "unknown4", "unknown5"])
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"].upper().split(" ZONE SUBSTATION", 1)[0].split(" TERMINAL STATION", 1)[0]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_ZONE, properties)
            if properties["ref"] in features_dict.keys():
                properties["name"] = features_dict[properties["ref"]]["name"]
                if voltages_str := features_dict[properties["ref"]]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if capacity_mva := features_dict[properties["ref"]]["capacity_mva"]:
                    properties["extras"]["rating"] = f"{capacity_mva} MVA"
            items.append(Feature(**properties))
        return items

    def parse_transformers(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": str(feature["ID"]),
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            apply_category(Categories.TRANSFORMER, properties)
            if capacity_kva := feature.get("MDIC_KVA"):
                properties["extras"]["rating"] = f"{capacity_kva} kVA"
            items.append(Feature(**properties))
        return items
