from locations.spiders.sky_zone import SkyZoneSpider


class DefyUSSpider(SkyZoneSpider):
    name = "defy_us"
    item_attributes = {"name": "DEFY", "brand": "DEFY", "brand_wikidata": "Q138674066"}
    start_urls = ["https://defy.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
