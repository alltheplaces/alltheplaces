from locations.storefinders.locally import LocallySpider


class AsicsUsSpider(LocallySpider):
    name = "asics_us"
    item_attributes = {"brand": "ASICS", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = [
        "https://www.locally.com/stores/conversion_data?has_data=true&company_id=1682&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=31.945163222857545&map_center_lng=-96.352774663203&map_distance_diag=2692.1535387671056&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=5"
    ]
