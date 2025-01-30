import re
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

class HobsonsBayCityCouncilTreesAUSpider(JSONBlobSpider):
    name = "hobsons_bay_city_council_trees_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    allowed_domains = ["services3.arcgis.com"]
    start_urls = ["https://services3.arcgis.com/gToGKwidNkZbWBGJ/ArcGIS/rest/services/Trees_point/FeatureServer/0/query?where=1%3D1&objectIds=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=*&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=4326&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&collation=&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=0&resultRecordCount=2000&returnZ=false&returnM=false&returnTrueCurves=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="]
    locations_key = "features"

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        yield from super().parse_feature_array(response, feature_array)
        if len(feature_array) == 2000:
            # More results exist and need to be queried for.
            current_offset = str(int(response.request.url.split("resultOffset=", 1)[1].split("&", 1)[0]) + 2000)
            yield Request(url=self.start_urls[0].replace("resultOffset=0", f"resultOffset={current_offset}"), dont_filter=True)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Central_As"]
        item["addr_full"] = re.sub(r"\s+", " ", feature["Feature_Lo"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["taxon:en"] = feature["T_Common_N"]
        item["extras"]["genus"] = feature["T_Genus"]
        item["extras"]["species"] = feature["T_Species"]
        item["extras"]["height"] = feature["T_Tree_Hei"]
        item["extras"]["protected"] = "yes"
        yield item
