from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class CinnabonSASpider(AgileStoreLocatorSpider):
    name = "cinnabon_sa"
    item_attributes = {"brand": "Cinnabon", "brand_wikidata": "Q1092539"}
    allowed_domains = ["cinnabon-ksa.com"]

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
