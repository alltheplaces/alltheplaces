from locations.storefinders.elfsight import ElfsightSpider


class BootleggerCoffeeCompanySpider(ElfsightSpider):
    name = "bootlegger_coffee_company"
    item_attributes = {"brand": "Bootlegger Coffee Company", "brand_wikidata": "Q116646503"}
    host = "shy.elfsight.com"
    shop = "bootlegger-coffee.myshopify.com"
    api_key = "8212fde6-c29c-44b5-bc63-5ebddf7f3b40"
    no_refs = True  # not all locations seem to have an id

    def post_process_item(self, item, response, location):
        item["branch"] = location.pop("infoTitle")
        if "COMING SOON" not in item["branch"]:
            yield item
