from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class RepettoSpider(JSONBlobSpider):
    name = "repetto"
    item_attributes = {
        "brand": "Repetto",
        "brand_wikidata": "Q3427237",
    }
    start_urls = ["https://xnkosumdt5.execute-api.eu-west-3.amazonaws.com/prod/getStoreLocators"]

    # Map French country names to ISO codes
    COUNTRY_MAPPING = {
        "France": "FR",
        "Belgique": "BE",
        "Italie": "IT",
        "Canada": "CA",
        "Émirats arabes unis": "AE",
        "Danemark": "DK",
        "Japon": "JP",
        "Corée du Sud": "KR",
        "États-Unis": "US",
        "Suisse": "CH",
        "Allemagne": "DE",
        "Espagne": "ES",
        "Australie": "AU",
        "Turquie": "TR",
        "Irlande": "IE",
        "Norvège": "NO",
        "Autriche": "AT",
        "Chypre": "CY",
        "Colombie": "CO",
    }

    def post_process_item(self, item, response, location):
        item["ref"] = item.get("name")
        item["branch"] = item.pop("name", "")

        # Map French country names to ISO codes
        if "country" in item:
            item["country"] = self.COUNTRY_MAPPING.get(item["country"], item["country"])

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
