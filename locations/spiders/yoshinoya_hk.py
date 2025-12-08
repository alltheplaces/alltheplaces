from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class YoshinoyaHKSpider(WPStoreLocatorSpider):
    name = "yoshinoya_hk"
    item_attributes = {"brand": "Yoshinoya", "brand_wikidata": "Q776272"}
    allowed_domains = ["www.yoshinoya.com.hk"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
