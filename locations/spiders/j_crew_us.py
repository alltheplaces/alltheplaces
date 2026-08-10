from locations.storefinders.yext import YextSpider


class JCrewUSSpider(YextSpider):
    name = "j_crew_us"
    item_attributes = {"brand": "J.Crew", "brand_wikidata": "Q5370765"}
    api_key = "c0963a72b0de0906e149ff1daac427d0"
