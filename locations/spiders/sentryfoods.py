from locations.storefinders.freshop import FreshopSpider


class SentryFoodsSpider(FreshopSpider):
    name = "sentryfoods"
    item_attributes = {"brand": "Sentry Foods", "brand_wikidata": "Q7451397"}
    app_key = "sentry_stores"
