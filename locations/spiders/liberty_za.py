from locations.storefinders.location_bank import LocationBankSpider


class LibertyZASpider(LocationBankSpider):
    name = "liberty_za"
    client_id = "46c362cd-08f6-49ff-8997-c5ed1ac50b2e"
    item_attributes = {"brand": "Liberty Group Limited", "brand_wikidata": "Q120885250"}

    def post_process_item(self, item, response, location):
        item["name"] = item.pop("branch")
        yield item
