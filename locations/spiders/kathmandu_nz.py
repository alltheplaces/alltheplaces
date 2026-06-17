from locations.storefinders.amai_promap import AmaiPromapSpider


class KathmanduNZSpider(AmaiPromapSpider):
    name = "kathmandu_nz"
    item_attributes = {"brand": "Kathmandu", "brand_wikidata": "Q1736294"}
    start_urls = ["https://www.kathmandu.co.nz/pages/stores"]
