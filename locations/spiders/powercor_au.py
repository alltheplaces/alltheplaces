import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class PowercorAUSpider(RosettaAPRSpider):
    name = "powercor_au"
    item_attributes = {"operator": "Powercor", "operator_wikidata": "Q7236677"}
    start_urls = ["https://dapr.powercor.com.au/"]
    data_files = [
        RosettaAPRDataFile(
            url="https://content.rosettaanalytics.com.au/citipower_powercor_layers_serve/CitiPower_Powercor_Zone_Substations.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_zone_substations",
        ),
        RosettaAPRDataFile(
            url="https://content.rosettaanalytics.com.au/citipower_powercor_layers_serve/CitiPower_Powercor_Distribution_Substations_July_2024.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_transformers",
        ),
    ]

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": str(feature["id"]),
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="./powercor_data/powercor_tech_spec_zs_summer.csv",
            file_type="csv",
            encrypted=True,
            callback_function_name="parse_zone_substation_attribs",
            column_headings=[
                "name",
                "voltages",
                "total_capacity_mva",
                "unknown1",
                "unknown2",
                "unknown3",
                "unknown4",
                "unknown5",
                "unknown6",
                "unknown7",
                "unknown8",
            ],
        )
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"].removesuffix(" Zone Substation") + " ZS": x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_ZONE, properties)
            if properties["name"] in features_dict.keys():
                if voltages_str := features_dict[properties["name"]]["voltages"]:
                    voltages = list(
                        map(
                            lambda x: str(x),
                            sorted(
                                list(
                                    set(
                                        map(
                                            lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)
                                        )
                                    )
                                ),
                                reverse=True,
                            ),
                        )
                    )
                    properties["extras"]["voltage"] = ";".join(voltages)
                if total_capacity_mva := features_dict[properties["name"]]["total_capacity_mva"]:
                    properties["extras"]["rating"] = str(total_capacity_mva) + " MVA"
            items.append(Feature(**properties))
        return items

    def parse_transformers(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": str(feature["GIS_ID"]),
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="https://dapr.citipower.com.au/serve.php?file=./powercor_data/CitiPower_Powercor_Distribution_Substations_July_2024.csv",
            file_type="csv",
            encrypted=True,
            callback_function_name="parse_transformer_attribs",
        )
        return (items, next_data_file)

    def parse_transformer_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["GIS_ID"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.TRANSFORMER, properties)
            if properties["ref"] in features_dict.keys():
                properties["name"] = features_dict[properties["ref"]]["SUB_NAME"]
                if voltage := features_dict[properties["ref"]]["VOLTAGE"]:
                    if voltage != "unknown":
                        properties["extras"]["voltage:primary"] = voltage.replace("kV", "000").replace(" ", "")
                if rating := features_dict[properties["ref"]]["INSTALLED_"]:
                    if rating != "unknown":
                        properties["extras"]["rating"] = rating.replace(".0", "").replace(" ", "") + " kVA"
            items.append(Feature(**properties))
        return items
