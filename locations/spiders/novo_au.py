from locations.storefinders.metalocator import MetaLocatorSpider


class NovoAUSpider(MetaLocatorSpider):
    name = "novo_au"
    item_attributes = {"brand": "NOVO", "brand_wikidata": "Q120669012"}
    brand_id = "9067"
