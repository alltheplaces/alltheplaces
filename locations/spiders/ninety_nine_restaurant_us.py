from locations.storefinders.nomnom import NomNomSpider


class NinetyNineRestaurantUSSpider(NomNomSpider):
    name = "ninety_nine_restaurant_us"
    start_urls = ["https://order.99restaurants.com/api/restaurants"]
    item_attributes = {
        "brand": "Ninety Nine Restaurant & Pub",
        "brand_wikidata": "Q64358371",
    }
    use_calendar = False  # only shows the current day
    drop_attributes = {"website"}
