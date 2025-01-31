from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HobsonsBayCityCouncilSportPitchesAUSpider(JSONBlobSpider):
    name = "hobsons_bay_city_council_sport_pitches_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    allowed_domains = ["services3.arcgis.com"]
    start_urls = [
        "https://services3.arcgis.com/gToGKwidNkZbWBGJ/ArcGIS/rest/services/Recreation_Facilities_Pt/FeatureServer/0/query?where=1%3D1&objectIds=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=4326&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&collation=&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnTrueCurves=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["central_as"]
        item["name"] = feature["site_name"]
        apply_category(Categories.LEISURE_PITCH, item)

        match feature["feature_ty"]:
            case "PF-Basketball Courts":
                item["extras"]["sport"] = "basketball"
                item["extras"]["hoops"] = "2"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-Box Lacross":
                item["extras"]["sport"] = "lacrose"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-BMX Park":
                item["extras"]["sport"] = "bmx"
            case "PF-Cricket Nets":
                item["extras"]["sport"] = "cricket"
                item["extras"]["barrier"] = "fence"
            case "PF-Cricket Wicket":
                item["extras"]["sport"] = "cricket"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-Half Court":
                item["extras"]["sport"] = "basketball"
                item["extras"]["hoops"] = "1"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-Multi-Use Court":
                item["extras"]["sport"] = "multi"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-Netball Court":
                item["extras"]["sport"] = "netball"
                item["extras"]["hoops"] = "2"
                self.add_sports_pitch_surface_to_item(feature["HardCourtM"], item)
            case "PF-Skate Park":
                item["extras"]["sport"] = "skateboard"
            case "PF-Tennis Practice Wall":
                item["extras"]["sport"] = "tennis"
                item["extras"]["barrier"] = "wall"
            case _:
                raise ValueError("Unknown sports pitch type: {}".format(feature["feature_ty"]))

        yield item

    @staticmethod
    def add_sports_pitch_surface_to_item(surface_type: str, item: Feature) -> None:
        match surface_type:
            case "Asphalt":
                item["extras"]["surface"] = "asphalt"
            case "Concrete":
                item["extras"]["surface"] = "concrete"
            case "Synthetic":
                item["extras"]["surface"] = "acrylic"
            case "Synthetic Turf":
                item["extras"]["surface"] = "artificial_turf"
            case "Turf":
                item["extras"]["surface"] = "grass"
            case "Not Applicable":
                pass
            case _:
                raise ValueError("Unknown sports pitch surface type: {}".format(surface_type))
