from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class LoroITSpider(WpGoMapsSpider):
    name = "loro_it"
    item_attributes = {"brand": "Loro", "brand_wikidata": "Q131832194"}
    start_urls = [
        "https://www.loro.it/wp-json/wpgmza/v1/features/base64eJyrVkrLzClJLVKyUqqOUcpNLIjPTIlRsopRMopR0gEJFGeUFni6FAPFomOBAsmlxSX5uW6ZqTkpELFapVoABXgWuw"
    ]

    def post_process_item(self, item: Feature, location: dict) -> Feature:
        item["name"] = None
        apply_category(Categories.FUEL_STATION, item)
        return item
