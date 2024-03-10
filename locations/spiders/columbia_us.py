from locations.storefinders.locally import LocallySpider


class ColumbiaUsSpider(LocallySpider):
    name = "columbia_us"
    item_attributes = {"brand": "Columbia Sportswear Company", "brand_wikidata": "Q1112588"}
    allowed_domains = ["www.columbia.com"]
    start_urls = [
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&store_mode=&style=&color=&upc=&category=Brand&inline=1&show_links_in_list=&parent_domain=&map_ne_lat=48.60220231134477&map_ne_lng=-92.18225182145208&map_sw_lat=20.342279879097987&map_sw_lng=-135.99572838395235&map_center_lat=34.47224109522138&map_center_lng=-114.08899010270221&map_distance_diag=3000&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=67&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=4&lang=en-us&currency=USD",
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&store_mode=&style=&color=&upc=&category=Factory&inline=1&show_links_in_list=&parent_domain=&map_ne_lat=48.60220231134477&map_ne_lng=-92.18225182145208&map_sw_lat=20.342279879097987&map_sw_lng=-135.99572838395235&map_center_lat=34.47224109522138&map_center_lng=-114.08899010270221&map_distance_diag=3000&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=67&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=4&lang=en-us&currency=USD",
        "https://columbia.locally.com/stores/conversion_data?has_data=true&company_id=67&store_mode=&style=&color=&upc=&category=clearancestore&inline=1&show_links_in_list=&parent_domain=&map_ne_lat=48.60220231134477&map_ne_lng=-92.18225182145208&map_sw_lat=20.342279879097987&map_sw_lng=-135.99572838395235&map_center_lat=34.47224109522138&map_center_lng=-114.08899010270221&map_distance_diag=3000&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=67&only_store_id=false&uses_alt_coords=false&q=false&zoom_level=4&lang=en-us&currency=USD",
    ]
