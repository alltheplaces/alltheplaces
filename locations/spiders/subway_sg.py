from locations.spiders.subway import SubwaySpider
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SubwaySGSpider(AgileStoreLocatorSpider):
    name = "subway_sg"
    item_attributes = SubwaySpider.item_attributes
    start_urls = [
        "https://subwayisfresh.com.sg/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1",
    ]
