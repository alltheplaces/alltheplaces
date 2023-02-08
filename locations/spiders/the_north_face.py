from locations.storefinders.where2getit import Where2GetItSpider


class TheNorthFaceSpider(Where2GetItSpider):
    name = "the_north_face"
    item_attributes = {"brand": "The North Face", "brand_wikidata": "Q152784"}
    app_key = "C1907EFA-14E9-11DF-8215-BBFCBD236D0E"
    query = {"or": {"northface": {"eq": "1"}, "outletstore": {"eq": "1"}}}
