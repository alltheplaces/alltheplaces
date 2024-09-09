from locations.storefinders.location_bank import LocationBankSpider


class TymebankZASpider(LocationBankSpider):
    name = "tymebank_za"
    client_id = "05c109b0-604d-4570-9ecf-fee8f55b18fd"
    item_attributes = {
        "brand": "TymeBank",
        "brand_wikidata": "Q65066197",
        # "extras": Categories..value,
    }

    def post_process_item(self, item, response, location):
        item.pop("website")
        item["branch"] = item["branch"].removeprefix("Kiosk ")
        yield item
