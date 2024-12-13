from locations.storefinders.location_bank import LocationBankSpider


class SimplyAsiaZASpider(LocationBankSpider):
    name = "simply_asia_za"
    client_id = "9e487353-4db4-4096-bebf-79ebd729f60f"
    item_attributes = {"brand": "Simply Asia", "brand_wikidata": "Q130358521"}

    def post_process_item(self, item, response, location):
        item["website"] = "https://stores.simplyasia.co.za/details/" + location["storeLocatorDetailsShortURL"]
        yield item
