from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class MinnesotaDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "minnesota_department_of_transportation_us"
    item_attributes = {
        "operator": "Minnesota Department of Transportation",
        "operator_wikidata": "Q3315550",
        "state": "MN",
    }
    api_endpoint = "https://511mn.org/api/graphql"
    video_url_template = "https://video.dot.state.mn.us/public/{}.stream/playlist.m3u8"
    custom_settings = {"ROBOTSTXT_OBEY": False}
