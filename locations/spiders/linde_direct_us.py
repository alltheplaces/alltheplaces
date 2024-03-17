from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.rio_seo_spider import RioSeoSpider


class LindeDirectUSSpider(RioSeoSpider):
    name = "linde_direct_us"
    item_attributes = {"brand": "Linde Gas & Equipment", "brand_wikidata": "Q902780"}
    start_urls = [
        "https://maps.stores.lindedirect.com/api/getAsyncLocations?template=search&level=search&search=Kansas%20City,%20KS,%20US&radius=100000&limit=100000"
    ]

    