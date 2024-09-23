from locations.spiders.sleepmasters import SleepmastersSpider


class RussellsZASpider(SleepmastersSpider):
    name = "russells_za"
    item_attributes = {"brand": "Russells", "brand_wikidata": "Q116620465"}
    start_urls = ["https://www.russells.co.za/storelocator/"]
