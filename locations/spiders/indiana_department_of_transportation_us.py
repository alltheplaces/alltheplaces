from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class IndianaDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "indiana_department_of_transportation_us"
    item_attributes = {
        "operator": "Indiana Department of Transportation",
        "operator_wikidata": "Q4925393",
    }
    api_endpoint = "https://511in.org/api/graphql"
    video_url_template = "https://skysfs3.trafficwise.org/rtplive/{}/playlist.m3u8"
    custom_settings = {"ROBOTSTXT_OBEY": False}
