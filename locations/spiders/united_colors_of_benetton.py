from locations.storefinders.woosmap import WoosmapSpider


class UnitedColorsOfBenettonSpider(WoosmapSpider):
    name = "united_colors_of_benetton"
    item_attributes = {"brand": "United Colors of Benetton", "brand_wikidata": "Q817139"}
    key = "woos-77ab54a0-3d40-3188-8f64-58f02485a654"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Origin": "https://world.benetton.com/"}}