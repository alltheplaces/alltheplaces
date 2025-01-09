import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class EssentialEnergyAUSpider(RosettaAPRSpider):
    name = "essential_energy_au"
    item_attributes = {"operator": "Essential Energy", "operator_wikidata": "Q17003842"}
    start_urls = ["https://dapr.essentialenergy.com.au/"]
    data_files = [
        RosettaAPRDataFile(
            url="./layers/Zone_Substations_Essential.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_zone_substations",
        ),
        RosettaAPRDataFile(
            url="./layers/Supply_Point_Station_Essential.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_bulk_supply_points",
        ),
    ]

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            if feature.get("asset_code"):
                ref = feature["asset_code"]
            elif feature.get("sbuiltenv_transmissionsubstatio"):
                ref = str(feature["sbuiltenv_transmissionsubstatio"])
            else:
                ref = feature["asset_name"]
            properties = {
                "ref": ref,
                "name": feature["asset_name"],
                "city": feature["suburb"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="./essential_data/Zone_Substation_Data_Technical_Essential.csv",
            file_type="csv",
            encrypted=True,
            callback_function_name="parse_zone_substation_attribs",
            column_headings=[
                "name",
                "voltages",
                "transformer_1_capacity_mva",
                "transformer_2_capacity_mva",
                "transformer_3_capacity_mva",
            ],
        )
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
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
                transformer_capacities = []
                # Transformer capacities are provided as two or three values
                # e.g. "10/15" or "10/15/20". It is not known what each of
                # these numbers are, but it is assumed to be similar to the
                # following types of capacity measurement methods:
                # 1. ONAN: Oil Natural Air Natural
                # 2. ONAF: Oil Natural Air Forced
                # 3. CMR: Continuous Maximum Rating
                # 4. CER: Continuous Emergency Rating
                # This code keeps things simple and just picks the biggest
                # number supplied for each transformer.
                if transformer_1_capacity_mva_str := features_dict[properties["name"]]["transformer_1_capacity_mva"]:
                    transformer_1_capacities = sorted(
                        list(
                            set(map(lambda x: float(x), re.findall(r"(\d+(?:\.\d+)?)", transformer_1_capacity_mva_str)))
                        ),
                        reverse=True,
                    )
                    if len(transformer_1_capacities) >= 1:
                        transformer_capacities.append(transformer_1_capacities[0])
                if transformer_2_capacity_mva_str := features_dict[properties["name"]]["transformer_2_capacity_mva"]:
                    transformer_2_capacities = sorted(
                        list(
                            set(map(lambda x: float(x), re.findall(r"(\d+(?:\.\d+)?)", transformer_2_capacity_mva_str)))
                        ),
                        reverse=True,
                    )
                    if len(transformer_2_capacities) >= 1:
                        transformer_capacities.append(transformer_2_capacities[0])
                if transformer_3_capacity_mva_str := features_dict[properties["name"]]["transformer_3_capacity_mva"]:
                    transformer_3_capacities = sorted(
                        list(
                            set(map(lambda x: float(x), re.findall(r"(\d+(?:\.\d+)?)", transformer_3_capacity_mva_str)))
                        ),
                        reverse=True,
                    )
                    if len(transformer_3_capacities) >= 1:
                        transformer_capacities.append(transformer_3_capacities[0])
                if len(transformer_capacities) > 1:
                    total_capacity_mva = str(sum(transformer_capacities)) + " MVA"
                    properties["extras"]["rating"] = total_capacity_mva
            items.append(Feature(**properties))
        return items

    def parse_bulk_supply_points(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": feature["asset_name"],
                "name": feature["asset_name"],
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            items.append(Feature(**properties))
        return items
