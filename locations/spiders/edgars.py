from locations.storefinders.amai_promap import AmaiPromapSpider


class EdgarsSpider(AmaiPromapSpider):
    name = "edgars"
    start_urls = ["https://www.edgars.co.za/pages/store-locator"]
    item_attributes = {"brand": "Edgars", "brand_wikidata": "Q97276073"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        yield item
