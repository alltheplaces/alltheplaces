from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo_spider import RioSeoSpider


class CommerceBankUSSpider(RioSeoSpider):
    name = "commerce_bank_us"
    item_attributes = {"brand": "Commerce Bank", "brand_wikidata": "Q5152411"}
    allowed_domains = ["locations.commercebank.com"]
    start_urls = [
        "https://maps.locations.commercebank.com/api/getAsyncLocations?template=domain&level=domain&radius=10000&limit=3000"
    ]

    def post_process_feature(self, feature, location):
        # TODO: Is name reliable?
        if feature["name"] == "Commerce Bank ATM":
            apply_category(Categories.ATM, feature)
        else:
            apply_category(Categories.BANK, feature)

        return feature
