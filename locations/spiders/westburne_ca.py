from locations.storefinders.rexel import RexelSpider


class WestburneCASpider(RexelSpider):
    name = "westburne_ca"
    item_attributes = {"brand": "Westburne (Canada)", "brand_wikidata": "Q"}
    base_url = "www.westburne.ca/cwr"
    search_lat = 51
    search_lon = 85
