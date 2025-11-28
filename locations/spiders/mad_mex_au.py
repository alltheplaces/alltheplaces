from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class MadMexAUSpider(SuperStoreFinderSpider):
    name = "mad_mex_au"
    item_attributes = {"brand_wikidata": "Q19589766"}
    allowed_domains = ["www.madmex.com.au"]
