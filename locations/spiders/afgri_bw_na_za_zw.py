from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class AfgriBWNAZAZWSpider(AgileStoreLocatorSpider):
    name = "afgri_bw_na_za_zw"
    item_attributes = {"brand": "AFGRI Equipment", "brand_wikidata": "Q119264464"}
    allowed_domains = ["afgriequipment.co.za"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "")
        yield item
