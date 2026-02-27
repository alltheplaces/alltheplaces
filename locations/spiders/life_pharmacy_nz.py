from locations.storefinders.stockist import StockistSpider


class LifePharmacyNZSpider(StockistSpider):
    name = "life_pharmacy_nz"
    key = "u22846"
    item_attributes = {"brand": "Life Pharmacy", "brand_wikidata": "Q7180825"}

    def parse_item(self, item, location):
        item["branch"] = item.pop("name").removeprefix("Life Pharmacy ")
        try:
            item["website"] = location["custom_fields"][2]["value"]
        except IndexError:
            pass
        yield item
