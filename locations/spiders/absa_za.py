from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class AbsaZASpider(JSONBlobSpider):
    name = "absa_za"
    item_attributes = {"brand": "ABSA", "brand_wikidata": "Q58641733"}
    start_urls = ["https://www.absa.co.za/etc/barclays/contact-info/south-africa/_jcr_content/locations.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, location):
        if location["type"] == "branch":
            apply_category(Categories.BANK, item)
        elif location["type"] == "atm":
            apply_category(Categories.ATM, item)
        else:
            # there are a number of "dealer" types, ignore
            return
        yield item
