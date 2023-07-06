from locations.storefinders.metalocator import MetaLocatorSpider


class BettsAU(MetaLocatorSpider):
    name = "betts_au"
    item_attributes = {"brand": "Betts", "brand_wikidata": "Q118555401"}
    brand_id = "6176"
    country_list = ["Australia"]
