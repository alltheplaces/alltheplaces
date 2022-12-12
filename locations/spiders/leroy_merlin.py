from locations.storefinders.woosmap import WoosmapSpider


class LeroyMerlin(WoosmapSpider):
    name = "leroy_merlin"
    item_attributes = {"brand": "Leroy Merlin", "brand_wikidata": "Q889624"}
    key = "woos-47262215-fc76-3bd2-8e0d-d8fda2544349&_=1670855900"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://www.leroymerlin.fr/"}}
