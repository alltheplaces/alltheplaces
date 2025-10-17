from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class TakkoFashionSpider(UberallSpider):
    name = "takko_fashion"
    item_attributes = {"brand": "Takko Fashion", "brand_wikidata": "Q1371302"}
    key = "ntntW06QJjYNYFkpc7H8w3P7V2Q9kb"

    def post_process_item(self, item: Feature, response, location: dict, **kwargs):
        item["ref"] = str(location["id"])
        slug = (
            "/".join([item["city"], location["streetAndNumber"] or "", location["identifier"]])
            .lower()
            .replace(" ", "-")
        )
        item["website"] = "https://www.takko.com/de-de/stores/#!/l/" + slug
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
