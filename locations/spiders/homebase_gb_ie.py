

from locations.storefinders.uberall import UberallSpider

class HomebaseGBIESpider(UberallSpider):
    name = "homebase_gb_ie"
    item_attributes = {"brand": "Homebase", "brand_wikidata": "Q9293447"}
    key = "uryD0GjzSwZ7dbDQkmUpVvnwMkL4lh"
