from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class IowaDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "iowa_department_of_transportation_us"
    item_attributes = {
        "operator": "Iowa Department of Transportation",
        "operator_wikidata": "Q4925621",
        "state": "IA",
    }
    api_endpoint = "https://www.511ia.org/api/graphql"
    video_url_template = "https://iowadotsfs2.us-east-1.skyvdn.com/rtplive/{}/playlist.m3u8"
    custom_settings = {"ROBOTSTXT_OBEY": False}
