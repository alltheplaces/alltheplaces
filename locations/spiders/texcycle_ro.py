from locations.spiders.texcycle_bg import TexcycleBGSpider


class TexcycleROSpider(TexcycleBGSpider):
    name = "texcycle_ro"
    allowed_domains = ["www.texcycle.ro"]
    start_urls = ["https://texcycle.ro/locations/"]
