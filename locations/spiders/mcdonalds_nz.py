from locations.spiders.mcdonalds_eg import McdonaldsEGSpider


class McdonaldsNZSpider(McdonaldsEGSpider):
    name = "mcdonalds_nz"
    allowed_domains = ["mcdonalds.co.nz"]
    start_urls = ["https://mcdonalds.co.nz/data/store"]
