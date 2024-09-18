from locations.storefinders.amai_promap import AmaiPromapSpider


class DunnsSpider(AmaiPromapSpider):
    name = "dunns"
    start_urls = ["https://www.dunns.co.za/pages/store-locator-dunns"]
    item_attributes = {"brand": "Dunns", "brand_wikidata": "Q116619823"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
