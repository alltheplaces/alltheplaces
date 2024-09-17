from locations.spiders.legit_za import LegitZASpider


class DunnsSpider(LegitZASpider):
    name = "dunns"
    start_urls = ["https://www.dunns.co.za/pages/store-locator-dunns"]
    item_attributes = {"brand": "Dunns", "brand_wikidata": "Q116619823"}
