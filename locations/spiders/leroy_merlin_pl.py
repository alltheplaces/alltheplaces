from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider


class LeroyMerlinPLSpider(WoosmapSpider):
    name = "leroy_merlin_pl"
    item_attributes = {"brand": "Leroy Merlin", "brand_wikidata": "Q889624"}
    key = "woos-936f7dae-38cd-3785-8a3c-153b43bd33ca"
    origin = "https://www.leroymerlin.pl"

    def parse_item(self, item, feature, **kwargs):
        item.pop("name", None)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
