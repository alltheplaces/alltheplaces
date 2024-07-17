from locations.storefinders.rio_seo import RioSeoSpider


class HallmarkSpider(RioSeoSpider):
    name = "hallmark"
    item_attributes = {"brand": "Hallmark", "brand_wikidata": "Q1521910"}
    allowed_domains = ["maps.hallmark.com"]
    start_urls = [
        "https://maps.hallmark.com/api/getAsyncLocations?template=search&level=search&search=66952&radius=10000&limit=3000"
    ]
