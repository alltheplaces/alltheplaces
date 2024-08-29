import json

# Field mapping for converting GeoJSON properties to JSON Lines fields
FIELD_MAPPING = {
    "@spider": "spider",
    "ref": "ref",
    "@source_uri": "source_uri",
    "name": "name",
    "branch": "branch",
    "brand": "brand",
    "brand:wikidata": "brand_wikidata",
    "nsi_id": "nsi_id",
    "shop": "shop",
    "amenity": "amenity",
    "addr:country": "country",
    "addr:full": "addr_full",
    "located_in": "located_in",
    "located_in:wikidata": "located_in_wikidata",
    "addr:housenumber": "housenumber",
    "addr:street_address": "street_address",
    "addr:street": "street",
    "addr:city": "city",
    "addr:state": "state",
    "addr:postcode": "postcode",
    "website": "website",
    "email": "email",
    "contact:facebook": "facebook",
    "contact:twitter": "twitter",
    "phone": "phone",
    "opening_hours": "opening_hours",
    "image": "image",
    "operator": "operator",
    "operator:wikidata": "operator_wikidata",
    "end_date": "end_date",
}


def convert_geojson_to_jsonlines(geojson_data: dict) -> list:
    """
    Convert GeoJSON data to JSON Lines format.

    Args:
        geojson_data (dict): The GeoJSON data to be converted.

    Returns:
        list: A list of JSON Lines formatted strings, each representing a feature in the GeoJSON data.
              Returns None if the input data is invalid or contains no features.
    """
    if not geojson_data or "features" not in geojson_data or not geojson_data["features"]:
        return None

    jsonlines = []

    for feature in geojson_data["features"]:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Map properties based on the defined FIELD_MAPPING
        jsonline = {
            output_key: properties.get(geojson_key)
            for geojson_key, output_key in FIELD_MAPPING.items()
            if geojson_key in properties
        }

        if geometry and "coordinates" in geometry and geometry["type"] == "Point":
            jsonline["geometry"] = f"POINT ({geometry['coordinates'][0]} {geometry['coordinates'][1]})"
            jsonline["lat"] = str(geometry["coordinates"][1])
            jsonline["lon"] = str(geometry["coordinates"][0])

        if "@spider" in properties:
            jsonline["extras"] = [{"key": "spider", "value": properties["@spider"]}]

        # Filter out None values and convert the dictionary to a JSON string
        filtered_jsonline = {k: v for k, v in jsonline.items() if v is not None}
        jsonlines.append(json.dumps(filtered_jsonline))

    return jsonlines
