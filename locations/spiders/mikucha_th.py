from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider


class MikuchaTHSpider(WordpressHeronFoodsSpider):
    name = "mikucha_th"
    item_attributes = {
        "brand_wikidata": "Q118640408",
        "brand": "Mikucha",
    }
    radius = 1000
    domain = "mikucha.co.th"
    lat = 13.7563309
    lon = 100.5017651
