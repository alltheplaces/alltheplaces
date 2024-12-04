from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class ColoradoDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "colorado_department_of_transportation_us"
    item_attributes = {
        "operator": "Colorado Department of Transportation",
        "operator_wikidata": "Q2112717",
    }
    api_endpoint = "https://maps.cotrip.org/api/graphql"
    video_url_template = "https://publicstreamer2.cotrip.org/rtplive/{}/playlist.m3u8"
    custom_settings = {"ROBOTSTXT_OBEY": False}
