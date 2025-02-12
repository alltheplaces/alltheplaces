from locations.spiders.cycle_lab_za import CycleLabZASpider


class TheProShopZASpider(CycleLabZASpider):
    name = "the_pro_shop_za"
    item_attributes = {"brand": "The Pro Shop", "brand_wikidata": "Q130488660"}
    start_urls = ["https://www.theproshop.co.za/store"]
    download_timeout = 30
