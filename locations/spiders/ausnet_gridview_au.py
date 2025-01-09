from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rosetta_apr import RosettaAPRDataFile, RosettaAPRSpider


class AusnetGridviewAUSpider(RosettaAPRSpider):
    name = "ausnet_gridview_au"
    item_attributes = {"operator": "AusNet", "operator_wikidata": "Q7392701"}
    start_urls = ["https://gridview.ausnetservices.com.au/"]
    data_files = [
        RosettaAPRDataFile(
            url="https://content.rosettaanalytics.com.au/ausnet_gridview_layers_serve_2024/Ausnet_Victorian_Distribution_Substations.geojson",
            file_type="geojson",
            encrypted=True,
            callback_function_name="parse_transformers_geojson",
        ),
    ]
    requires_proxy = "AU"

    def parse_transformers_geojson(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile):
        items = []
        for feature in features:
            properties = {
                "ref": feature["Name"],
                "geometry": feature["geometry"],
            }
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="./ausnet_data/distribution_substation_data.csv",
            file_type="csv",
            encrypted=True,
            callback_function_name="parse_transformers_csv",
            column_headings=["id", "name", "capacity_kva"],
        )
        return (items, next_data_file)

    def parse_transformers_csv(
        self, features: list[dict], existing_features: list[dict]
    ) -> (list[dict], RosettaAPRDataFile):
        items = []
        features_dict = {x["id"]: x for x in features}
        for properties in existing_features:
            apply_category(Categories.TRANSFORMER, properties)
            if properties["ref"] in features_dict.keys():
                properties["name"] = features_dict[properties["ref"]]["name"].strip()
                if capacity_kva := features_dict[properties["ref"]]["capacity_kva"].strip():
                    properties["extras"]["rating"] = f"{capacity_kva} kVA"
            items.append(properties)
        next_data_file = RosettaAPRDataFile(
            url="https://gridview.ausnetservices.com.au/ausnet_data/distribution_substation_mapping.zip",
            file_type="csv",
            encrypted=False,
            callback_function_name="parse_transformers_zip",
            archive_format="zip",
            archive_filename="distribution_substation_mapping.csv",
        )
        return (items, next_data_file)

    def parse_transformers_zip(self, features: list[dict], existing_features: list[dict]) -> list[Feature]:
        items = []
        features_dict = {x["SUBSTATION"]: x for x in features}
        for properties in existing_features:
            if properties["ref"] in features_dict.keys():
                new_name = features_dict[properties["ref"]]["NAME"].strip()
                if properties.get("name") and properties["name"] != new_name:
                    properties["extras"]["alt_name"] = new_name
                else:
                    properties["name"] = new_name
            items.append(Feature(**properties))
        return items
