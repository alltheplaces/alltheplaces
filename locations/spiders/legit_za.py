from locations.storefinders.amai_promap import AmaiPromapSpider


class LegitZASpider(AmaiPromapSpider):
    name = "legit_za"
    start_urls = ["https://www.legit.co.za/pages/store-locator"]
    item_attributes = {"brand": "LEGiT", "brand_wikidata": "Q122959274"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
