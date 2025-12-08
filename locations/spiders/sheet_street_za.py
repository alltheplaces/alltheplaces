from locations.spiders.miladys_za import MiladysZASpider


class SheetStreetZASpider(MiladysZASpider):
    name = "sheet_street_za"
    allowed_domains = ["www.sheetstreet.com"]
    start_urls = ["https://www.sheetstreet.com/store-locator"]
    item_attributes = {
        "brand": "Sheet Street",
        "brand_wikidata": "Q118185878",
    }
