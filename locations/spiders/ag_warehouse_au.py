from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class AgWarehouseAUSpider(AgileStoreLocatorSpider):
    name = "ag_warehouse_au"
    item_attributes = {"brand": "AG Warehouse", "brand_wikidata": "Q119261591"}
    allowed_domains = ["www.agwarehouse.com.au"]
