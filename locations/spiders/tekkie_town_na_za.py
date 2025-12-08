from locations.storefinders.amai_promap import AmaiPromapSpider


class TekkieTownNAZASpider(AmaiPromapSpider):
    name = "tekkie_town_na_za"
    start_urls = ["https://tekkietown.co.za/pages/store-locator"]
    item_attributes = {"brand": "Tekkie Town", "brand_wikidata": "Q116620895"}

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip().replace("  ", " ")
        item.pop("email")
        yield item
