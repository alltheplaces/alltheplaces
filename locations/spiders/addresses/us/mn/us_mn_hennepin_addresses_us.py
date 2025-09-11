from typing import Iterable

from scrapy.http import Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.storefinders import arcgis_feature_server


def join_non_null(*values, sep=""):
    return sep.join(str(v) for v in values if v is not None)


class UsMnHennepinAddressesUSSpider(arcgis_feature_server.ArcGISFeatureServerSpider, AddressSpider):
    name = "us_mn_hennepin_addresses_us"
    # https://gis.hennepin.us/arcgis/rest/services/HennepinData/LAND_PROPERTY/MapServer/0
    host = "gis.hennepin.us"
    context_path = "arcgis"
    service_id = "HennepinData/LAND_PROPERTY"
    server_type = "MapServer"
    layer_id = "0"
    item_attributes = {"state": "MN", "country": "US"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["housenumber"] = join_non_null(feature.get("ANUMBER"), feature.get("ANUMBERSUF"))
        item["street"] = join_non_null(
            feature.get("ST_PRE_MOD"),
            feature.get("ST_PRE_DIR"),
            feature.get("ST_PRE_TYP"),
            feature.get("ST_NAME"),
            feature.get("ST_POS_TYP"),
            feature.get("ST_POS_DIR"),
            feature.get("ST_POS_MOD"),
            sep=" ",
        )
        item["postcode"] = join_non_null(feature.get("ZIP"), feature.get("ZIP4"), sep="-")
        item["extras"]["addr:unit"] = (
            join_non_null(feature.get("SUB_AD_TYP"), feature.get("SUB_AD_ID"), sep=" ") or None
        )
        item["city"] = feature.get("MUNI_NAME")
        yield item
