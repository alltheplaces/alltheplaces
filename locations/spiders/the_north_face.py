from locations.storefinders.where2getit import Where2GetItSpider

# The spider gets Stores and Outlets
# A single query for CA collects both CA and US


class TheNorthFaceSpider(Where2GetItSpider):
    name = "the_north_face"
    item_attributes = {"brand": "The North Face", "brand_wikidata": "Q152784"}
    w2gi_id = "C1907EFA-14E9-11DF-8215-BBFCBD236D0E"
    w2gi_filter = {"or": {"northface": {"eq": "1"}, "outletstore": {"eq": "1"}}}
    w2gi_query = "CA"
