from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EnergexStreetCabinetsAUSpider(JSONBlobSpider):
    name = "energex_street_cabinets_au"
    item_attributes = {"operator": "Energex", "operator_wikidata": "Q5376841"}
    allowed_domains = ["services.arcgis.com"]
    start_urls = [
        "https://services.arcgis.com/bfVzktoY0OhzQCDj/ArcGIS/rest/services/Network_Energex/FeatureServer/3/query?where=1%3D1&objectIds=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&collation=&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=0&resultRecordCount=1000&returnZ=false&returnM=false&returnTrueCurves=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]
    locations_key = "features"

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        yield from super().parse_feature_array(response, feature_array)
        if len(feature_array) == 1000:
            # More results exist and need to be queried for.
            current_offset = str(int(response.request.url.split("resultOffset=", 1)[1].split("&", 1)[0]) + 1000)
            yield Request(
                url=self.start_urls[0].replace("resultOffset=0", f"resultOffset={current_offset}"), dont_filter=True
            )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SITE_REF"]
        apply_category(Categories.STREET_CABINET_POWER, item)
        yield item
