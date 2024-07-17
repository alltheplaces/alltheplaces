from locations.storefinders.rio_seo import RioSeoSpider


class LindeDirectUSSpider(RioSeoSpider):
    name = "linde_direct_us"
    item_attributes = {"brand": "Linde", "brand_wikidata": "Q902780"}
    start_urls = [
        "https://maps.stores.lindedirect.com/api/getAsyncLocations?template=search&level=search&search=Kansas%20City,%20KS,%20US&radius=100000&limit=100000"
    ]
