import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class TransgridAUSpider(RosettaAPRSpider):
    name = "transgrid_au"
    item_attributes = {"operator": "TransGrid", "operator_wikidata": "Q7833620"}
    start_urls = ["https://tapr.transgrid.com.au/"]
    data_files = [
        RosettaAPRDataFile(url="./layers/Transmission_Sub_Station_Transgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_transmission_substations"),
        RosettaAPRDataFile(url="./layers/Bulk_Supply_Points_Transgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_bulk_supply_points"),
        RosettaAPRDataFile(url="./layers/Generation_Transgrid.geojson", file_type="geojson", encrypted=True, callback_function_name="parse_generator_substations"),
    ]

    def parse_transmission_substations(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"].replace("\/", "/"),
                "name": feature["Name"].replace("\/", "/"),
                "geometry": feature["geometry"],
                "city": feature["SITESUBURB"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d{2,}(?:\.\d+)?)", properties["name"])))), reverse=True)))
            if len(voltages) >= 1:
                properties["extras"]["voltage"] = ";".join(voltages)
            elif feature.get("CAPACITY_kV"):
                properties["extras"]["voltage"] = str(int(float(feature["CAPACITY_kV"]) * 1000))
            items.append(Feature(**properties))
        return items

    def parse_bulk_supply_points(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
                "city": feature["SITESUBURB"],
            }
            apply_category(Categories.SUBSTATION_TRANSMISSION, properties)
            voltages = list(map(lambda x: str(x), sorted(list(set(map(lambda x: int(float(x) * 1000), re.findall(r"(\d{2,}(?:\.\d+)?)", properties["name"])))), reverse=True)))
            properties["extras"]["voltage"] = ";".join(voltages)
            items.append(Feature(**properties))
        return items

    def parse_generator_substations(self, features: list[dict]) -> list[Feature]:
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "name": feature["Name"],
                "geometry": feature["geometry"],
            }
            apply_category(Categories.SUBSTATION_GENERATION, properties)
            capacity_mva = sum(list(map(lambda x: int(float(x)), re.findall(r"(\d+(?:\.\d+)?)", re.sub(r"\([^\)]*\)", "", str(feature["Nameplate Rating"]))))))
            properties["extras"]["rating"] = f"{capacity_mva} MVA"
            items.append(Feature(**properties))
        return items
