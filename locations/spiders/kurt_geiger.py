from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider


class KurtGeigerSpider(YextAnswersSpider):
    name = "kurt_geiger"
    item_attributes = {"brand": "Kurt Geiger", "brand_wikidata": "Q17063744"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "kurt-geiger-search"
    api_key = "672f8261f70abeb66b9ce6c5c0572e7f"
    locale = "en-GB"

    def parse_item(self, location, item, **kwargs):
        item["website"] = urljoin("https://stores.kurtgeiger.com", location["slug"])
        apply_category(Categories.SHOP_SHOES, item)
        yield item
