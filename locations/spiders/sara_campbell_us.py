from locations.storefinders.stockinstore import StockInStoreSpider


class SaraCampbellUSSpider(StockInStoreSpider):
    name = "sara_campbell_us"
    item_attributes = {"brand": "Sara Campbell", "brand_wikidata": "Q117747597"}
    api_site_id = "10108"
    api_widget_id = "115"
    api_widget_type = "product"
    api_origin = "https://saracampbell.com"

    def parse_item(self, item, location):
        item["name"] = item["name"].replace("\xa0", " ")
        yield item
