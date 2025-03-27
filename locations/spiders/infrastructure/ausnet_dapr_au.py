import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class AusnetDaprAUSpider(RosettaAPRSpider):
    name = "ausnet_dapr_au"
    item_attributes = {"operator": "AusNet", "operator_wikidata": "Q7392701"}
    start_urls = ["https://dapr.ausnetservices.com.au/"]
    data_files = [
        RosettaAPRDataFile(
            url="./layers/Ausnet_Victorian_Zone_Substations.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_zone_substations",
        ),
        RosettaAPRDataFile(
            url="./layers/Ausnet_Victorian_Transmission_Terminal_Stations.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_transmission_substations",
        ),
    ]
    requires_proxy = "AU"

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": feature["asset_code"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_ZONE, properties)
            voltages = ";".join(
                map(
                    lambda x: str(int(float(x) * 1000)),
                    filter(None, [feature.get("sub_high_bus_voltage"), feature.get("sub_low_bus_voltage")]),
                )
            )
            properties["extras"]["voltage"] = voltages
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="./ausnet_data/Ausnet_Zone_Substations_Technical_Specifications.csv",
            file_type="csv",
            encrypted=True,
            callback_function_name="parse_zone_substation_attribs",
            column_headings=[
                "name",
                "transformers_count",
                "installed_capacity_mva",
                "nminus1_summer_capacity_mva",
                "nminus1_winter_capacity_mva",
                "load_transfers_2023",
                "embedded_generation_mw",
                "n_capacity_mva",
                "nminus1_capacity_mva",
                "nminus2_capacity_mva",
            ],
        )
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            short_name = properties["name"].removesuffix(" ZSS")
            if short_name in features_dict.keys():
                if installed_capacity_mva := features_dict[short_name]["installed_capacity_mva"]:
                    properties["extras"]["rating"] = f"{installed_capacity_mva} MVA"
            items.append(Feature(**properties))
        return items

    def parse_transmission_substations(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            if m := re.fullmatch(r"^([^\(]+) \(([^\)]+)\)$", feature["Name"]):
                full_name = m.group(1)
                abbrev_name = m.group(2)
            else:
                full_name = feature["Name"]
                abbrev_name = None

            if abbrev_name:
                ref = abbrev_name
            elif feature.get("FID"):
                ref = feature["FID"]
            else:
                self.logger.error(
                    "Could not detect assigned substation identifier. Unstable OBJECTID used as an identifier instead."
                )
                ref = feature["OBJECTID"]

            properties = {
                "ref": ref,
                "name": full_name,
                "geometry": feature["geometry"],
                "state": feature.get("STATE"),
            }
            if feature.get("SUBURB"):
                properties["city"] = feature["SUBURB"]
            elif feature.get("SITESUBURB"):
                properties["city"] = feature["SITESUBURB"]

            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)

            if abbrev_name:
                properties["extras"]["short_name"] = abbrev_name

            if feature.get("VOLTAGE"):
                properties["extras"]["voltage"] = str(int(float(feature["VOLTAGE"]) * 1000))
            elif feature.get("CAPACITY_kV"):
                properties["extras"]["voltage"] = str(int(float(feature["CAPACITY_kV"]) * 1000))

            items.append(Feature(**properties))
        return items
