from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NationalRegisterOfHistoricPlacesSpider(ArcGISFeatureServerSpider):
    name = "national_register_of_historic_places"
    # Works of the US federal government are not subject to copyright within
    # the United States, and the NPS confirms its own material is public
    # domain: https://www.nps.gov/aboutus/disclaimer.htm
    dataset_attributes = (
        ArcGISFeatureServerSpider.dataset_attributes
        | Licenses.US_PUBLIC_DOMAIN.value
        | {
            "attribution:name": "Cultural Resources GIS, National Park Service",
            "attribution:website": "https://www.nps.gov/subjects/nationalregister/index.htm",
        }
    )
    host = "mapservices.nps.gov"
    context_path = "arcgis"
    service_id = "cultural_resources/nrhp_locations"
    server_type = "MapServer"
    layer_id = "0"
    # Layer 1 of this service holds boundary polygons, mostly for historic
    # districts and other properties too large to map as a point. It is a
    # largely separate set: of its 19,405 listings only 451 also appear in the
    # point layer consumed here, so this spider covers roughly 70,500 of the
    # ~89,500 listings the service publishes.
    field_names = ["GEOM_ID", "NRIS_Refnum", "RESNAME", "ResType", "Address", "City", "State", "Is_NHL"]
    # STATUS is one of "Listed", "Removed" or null. Properties removed from the
    # register (usually following demolition) are excluded, as are the small
    # number of records with no status at all.
    where_query = "STATUS = 'Listed'"

    # NRHP resource types mapped onto OpenStreetMap `historic` values. "site"
    # and "structure" each span too much (battlefields, landscapes and ruins;
    # bridges, dams and ships) for a more specific tag to be correct.
    resource_types = {
        "building": {"historic": "building"},
        "district": {"historic": "district"},
        "object": {"historic": "monument"},
        "site": {"historic": "yes"},
        "structure": {"historic": "yes"},
    }

    # The register covers US states and territories, a handful of properties in
    # countries the United States formerly administered, and one in Morocco.
    # Territories and former territories have their own ISO 3166-1 codes, so
    # the spider name deliberately carries no country suffix and each item gets
    # an explicit country instead.
    countries = {
        "AMERICAN SAMOA": "AS",
        "FED. STATES": "FM",
        "GUAM": "GU",
        "MARSHALL ISLANDS": "MH",
        "MOROCCO": "MA",
        "N. MARIANA ISLANDS": "MP",
        "PALAU": "PW",
        "PUERTO RICO": "PR",
        "VIRGIN ISLANDS": "VI",
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # A single register listing can be mapped as several points, so the
        # NRHP reference number is not unique here (it collides for roughly
        # 1,500 of the points in this layer and would silently lose them to
        # the duplicate filter). GEOM_ID identifies one mapped location.
        item["ref"] = feature["GEOM_ID"].strip("{}")
        item["name"] = feature["RESNAME"]
        item["city"] = feature["City"]
        if country := self.countries.get(feature["State"]):
            # For these the source "State" names the territory itself, which
            # the country field already records. StateCodeCleanUpPipeline only
            # abbreviates US and Canadian states, so keeping it would emit raw
            # values such as "FED. STATES" next to country=FM.
            item["country"] = country
            item["state"] = None
        else:
            item["country"] = "US"
            item["state"] = feature["State"]
        item["website"] = "https://npgallery.nps.gov/AssetDetail/NRIS/{}".format(feature["NRIS_Refnum"])

        # DictParser maps the source "Address" field onto addr_full, but it
        # only ever holds the street portion of an address, so move it to
        # street_address. Values are descriptive rather than postal ("Jct. of
        # US 1 and SR 44") and are withheld for a few sensitive sites.
        item["addr_full"] = None
        address = feature["Address"]
        if address and "restricted" not in address.lower():
            item["street_address"] = address

        if category := self.resource_types.get(feature["ResType"]):
            apply_category(category, item)
        else:
            self.logger.warning("Unknown NRHP resource type `{}`.".format(feature["ResType"]))
            self.crawler.stats.inc_value("atp/{}/unhandled_resource_type/{}".format(self.name, feature["ResType"]))
            apply_category({"historic": "yes"}, item)

        # https://wiki.openstreetmap.org/wiki/Key:heritage - the National
        # Register is a national level designation, as is the National Historic
        # Landmark subset of it.
        item["extras"]["heritage"] = "2"
        item["extras"]["heritage:operator"] = "nhl;nrhp" if feature["Is_NHL"] == "X" else "nrhp"
        item["extras"]["ref:nrhp"] = feature["NRIS_Refnum"]

        yield item
