from locations.storefinders.metalocator import MetaLocatorSpider


class NovoNZSpider(MetaLocatorSpider):
    name = "novo_nz"
    item_attributes = {"brand": "NOVO", "brand_wikidata": "Q120669012"}
    brand_id = "9450"
    country_list = ["New Zealand"]
