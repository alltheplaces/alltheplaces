from locations.storefinders.storepoint import StorepointSpider


class AfgriEquipmentAUSpider(StorepointSpider):
    name = "afgri_equipment_au"
    item_attributes = {
        "brand": "AFGRI Equipment",
        "brand_wikidata": "Q119264464",
        "extras": {"shop": "tractor"},
    }
    key = "15f4466ee99d2b"

    def parse_item(self, item, location):
        item.pop("website")
        yield item
