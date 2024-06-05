from locations.spiders.mcdonalds_au import McDonaldsAUSpider


class McDonaldsNZSpider(McDonaldsAUSpider):
    name = "mcdonalds_nz"
    allowed_domains = ["mcdonalds.co.nz"]
    start_urls = ["https://mcdonalds.co.nz/data/store"]
