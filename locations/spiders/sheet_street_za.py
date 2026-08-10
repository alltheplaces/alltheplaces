from locations.spiders.miladys_za import MiladysZASpider


class SheetStreetZASpider(MiladysZASpider):
    name = "sheet_street_za"
    sitemap_urls = ["https://www.sheetstreet.com/media/sstsitemap.xml"]
    sitemap_rules = [(r"/sheet-street-[-\w]+-\d+$", "parse")]
    item_attributes = {
        "brand": "Sheet Street",
        "brand_wikidata": "Q118185878",
    }
