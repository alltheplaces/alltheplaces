from locations.storefinders.metalocator import MetaLocatorSpider


class NOVONZSpider(MetaLocatorSpider):
    name = "novo_nz"
    item_attributes = {"brand": "NOVO", "brand_wikidata": "Q120669012"}
    brand_id = "9450"
