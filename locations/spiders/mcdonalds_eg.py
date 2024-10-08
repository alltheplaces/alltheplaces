from locations.spiders.mcdonalds_au import McdonaldsAUSpider


class McdonaldsEGSpider(McdonaldsAUSpider):
    name = "mcdonalds_eg"
    allowed_domains = ["mcdonalds.eg"]
    start_urls = ["https://mcdonalds.eg/Stotes"]
