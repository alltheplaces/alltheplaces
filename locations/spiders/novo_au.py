from locations.storefinders.metalocator import MetaLocatorSpider


class NOVOAUSpider(MetaLocatorSpider):
    name = "novo_au"
    item_attributes = {"brand": "NOVO", "brand_wikidata": "Q120669012"}
    brand_id = "9067"
