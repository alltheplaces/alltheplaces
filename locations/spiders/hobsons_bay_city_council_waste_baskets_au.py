from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

class HobsonsBayCityCouncilWasteBasketsAUSpider(JSONBlobSpider):
    name = "hobsons_bay_city_council_waste_baskets_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    allowed_domains = ["services3.arcgis.com"]
    start_urls = ["https://services3.arcgis.com/gToGKwidNkZbWBGJ/ArcGIS/rest/services/Litter%20Bins_point/FeatureServer/0/query?where=1%3D1&objectIds=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=4326&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&collation=&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnTrueCurves=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["central_as"]
        apply_category(Categories.WASTE_BASKET, item)

        if feature["BinSize"] and feature["BinSize"].endswith(" Litres"):
            # "volume" is a made-up key that doesn't currently exist in OSM.
            # No other existing key for the volume of a bin appears to
            # currently exist in OSM.
            item["extras"]["volume"] = feature["BinSize"].lower()

        match feature["LitterBinM"]:
            case "Plastic":
                item["extras"]["material"] = "plastic"
            case "Stainless" | "Stainless/Steel":
                item["extras"]["material"] = "steel"
            case "Steel/Plastic":
                item["extras"]["material"] = "plastic;steel"
            case "Steel/Timber/Plastic":
                item["extras"]["material"] = "plastic;steel;wood"
            case "Not Applicable":
                pass
            case _:
                raise ValueError("Unknown waste basket material type: {}".format(feature["LitterBinM"]))

        yield item
