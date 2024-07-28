from locations.spiders.mcdonalds_au import McdonaldsAUSpider


class McdonaldsNZSpider(McdonaldsAUSpider):
    name = "mcdonalds_nz"
    allowed_domains = ["mcdonalds.co.nz"]
    start_urls = ["https://mcdonalds.co.nz/data/store"]
