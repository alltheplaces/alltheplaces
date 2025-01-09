import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class AusgridAUSpider(RosettaAPRSpider):
    name = "ausgrid_au"
    item_attributes = {"operator": "Ausgrid", "operator_wikidata": "Q4822750"}
    start_urls = ["https://dtapr.ausgrid.com.au/"]
    data_files = [
        RosettaAPRDataFile(url="./layers/Zone_Substations_Ausgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_zone_substations"),
        RosettaAPRDataFile(url="./layers/Transmission_Sub_Station_Ausgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_transmission_substations"),
        RosettaAPRDataFile(url="./layers/Supply_Point_Station_Ausgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_bulk_supply_points"),
        RosettaAPRDataFile(url="./layers/Switch_Station_Ausgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_switching_stations"),
    ]
    requires_proxy = "AU"

    def parse_ref_and_name(self, description: str) -> (str | None, str | None, str | None):
        """
        Extract a substation identifier, name and short name from the title of
        a substation provided in source data. The difference between a name
        and short name is the short name omits any voltage differentiator in
        the title and some punctuation and suffixes are removed.

        Examples:
          1. "ZN12345 ST. MOONVILLE 220kV STS" -> ("ZN12345", "ST. MOONVILLE 220kV STS", "ST MOONVILLE")
          2. "ZN12345 ST. MOONVILLE STS" -> ("ZN12345", "ST. MOONVILLE STS", "ST MOONVILLE")
          3. "ZN12345 ST. MOONVILLE" -> ("ZN12345", "ST. MOONVILLE", "ST MOONVILLE")
          3. "ZN12345" -> ("ZN12345", None, None)
        """
        ref = None
        name = None
        short_name = None
        if m := re.fullmatch(r"^([A-Z]{2}\d+) (.+)$", description):
            ref = m.group(1)
            name = m.group(2)
        elif m := re.fullmatch(r"^([A-Z]{2}\d+)$", description):
            ref = m.group(1)
            name = None
        else:
            self.logger.error("Could not detect assigned substation identifier from: \"{}\". Description/title used as an identifier instead.".format(description))
            ref = description
            name = description
        if name:
            name_words = re.split(r"\W+", name.replace(".", ""))
            for name_word in name_words:
                if name_word in ["STS"]:
                    break
                if re.search(r"\d+", name_word):
                    break
                if not short_name:
                    short_name = name_word
                else:
                    short_name = f"{short_name} {name_word}"
        return (ref, name, short_name)

    def parse_zone_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            ref, name, short_name = self.parse_ref_and_name(feature["Name"])
            properties = {
                "ref": ref,
                "name": name,
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./ausgrid_data/Technical_Specifiction_Summer_ZS.csv", file_type="csv", encrypted=True, callback_function_name="parse_zone_substation_attribs", column_headings=["name", "voltages", "total_capacity_mva", "firm_capacity_mva", "load_transfer_capacity_mva", "peak_load_exceeded_hours", "embedded_generation_solar_mw", "embedded_generation_other_mw"])
        return (items, next_data_file)

    def parse_zone_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_ZONE, properties)
            ref, name, short_name = self.parse_ref_and_name("{} {}".format(properties["ref"], properties["name"]))
            if short_name and short_name in features_dict.keys():
                if voltages_str := features_dict[short_name]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if total_capacity_mva := features_dict[short_name]["total_capacity_mva"]:
                    properties["extras"]["rating"] = f"{total_capacity_mva} MVA"
            items.append(Feature(**properties))
        return items

    def parse_transmission_substations(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            ref, name, short_name = self.parse_ref_and_name(feature["Name"])
            properties = {
                "ref": ref,
                "name": name,
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(url="./ausgrid_data/Technical_Specifiction_Summer_TX.csv", file_type="csv", encrypted=True, callback_function_name="parse_transmission_substation_attribs", column_headings=["name", "voltages", "total_capacity_mva", "firm_capacity_mva", "load_transfer_capacity_mva", "peak_load_exceeded_hours", "embedded_generation_solar_mw", "embedded_generation_other_mw"])
        return (items, next_data_file)

    def parse_transmission_substation_attribs(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["name"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            ref, name, short_name = self.parse_ref_and_name("{} {}".format(properties["ref"], properties["name"]))
            if short_name and short_name in features_dict.keys():
                if voltages_str := features_dict[short_name]["voltages"]:
                    voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d+(?:\.\d+)?)", voltages_str)))), reverse=True)))
                    properties["extras"]["voltage"] = ";".join(voltages)
                if total_capacity_mva := features_dict[short_name]["total_capacity_mva"]:
                    properties["extras"]["rating"] = f"{total_capacity_mva} MVA"
            items.append(Feature(**properties))
        return items

    def parse_bulk_supply_points(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            ref, name, short_name = self.parse_ref_and_name(feature["Name"])
            properties = {
                "ref": ref,
                "name": name,
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            properties["extras"]["voltage"] = feature["Voltage"].replace("kV", "000").replace(" ", "")
            items.append(Feature(**properties))
        return items

    def parse_switching_stations(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            ref, name, short_name = self.parse_ref_and_name(feature["Name"])
            properties = {
                "ref": ref,
                "name": name,
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            properties["extras"]["voltage"] = feature["Voltage"].replace("kV", "000").replace(" ", "")
            items.append(Feature(**properties))
        return items
