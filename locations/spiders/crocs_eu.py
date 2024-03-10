from locations.storefinders.locally import LocallySpider


class CrocsEUSpider(LocallySpider):
    name = "crocs_eu"
    item_attributes = {"brand": "Crocs", "brand_wikidata": "Q926699"}
    start_urls = [
        "https://crocs.locally.com/stores/conversion_data?has_data=true&company_id=1762&category=Outlet&inline=1&map_center_lat=46.661219&map_center_lng=2.587603&map_distance_diag=3000&sort_by=proximity&lang=en-gb",
        "https://crocs.locally.com/stores/conversion_data?has_data=true&company_id=1762&category=Store&inline=1&map_center_lat=46.661219&map_center_lng=2.587603&map_distance_diag=3000&sort_by=proximity&lang=en-gb",
    ]
    skip_auto_cc_spider_name = True

    def post_process_item(self, item, store):
        item["street_address"] = item.pop("addr_full")
