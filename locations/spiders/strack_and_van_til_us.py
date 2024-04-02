from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class StrackAndVanTilUSSpider(StoreLocatorPlusSelfSpider):
    name = "strack_and_van_til_us"
    item_attributes = {
        "brand_wikidata": "Q17108969",
        "brand": "Strack & Van Til",
    }
    allowed_domains = ["strackandvantil.com"]
    searchable_points_files = ["us_centroids_iseadgg_458km_radius.csv"]
    search_radius = 500
    max_results = 100
