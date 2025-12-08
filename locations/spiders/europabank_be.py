from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider


class EuropabankBESpider(JSONBlobSpider):
    name = "europabank_be"
    item_attributes = {
        "brand": "Europabank",
        "brand_wikidata": "Q2134017",
    }
    start_urls = ["https://www.europabank.be/WebsiteAPI/rest/offices/all"]

    def post_process_item(self, item, response, location):
        item["branch"] = location["kantoorNaam"]
        item["ref"] = location["kantoorNummer"]
        item["street_address"] = location["kantoorAdres"]
        item["city"] = location["kantoorStad"]
        item["postcode"] = str(location["kantoorPostNr"])
        item["phone"] = location["kantoorTelNr"]
        item["email"] = location["kantoorEmail"]
        item["website"] = f'https://www.europabank.be/nl/onze-kantoren/{location["url"]}'
        apply_yes_no(Extras.ATM, item, location["kantoorAutomaat"])
        apply_category(Categories.BANK, item)
        # TODO: parse hours
        yield item
