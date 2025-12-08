from locations.storefinders.castle_rock_oneweb import CastleRockOneWebSpider


class KansasDepartmentOfTransportationUSSpider(CastleRockOneWebSpider):
    name = "kansas_department_of_transportation_us"
    item_attributes = {
        "operator": "Kansas Department of Transportation",
        "operator_wikidata": "Q4925916",
        "state": "KS",
    }
    api_endpoint = "https://www.kandrive.gov/api/graphql"
    custom_settings = {"ROBOTSTXT_OBEY": False}
