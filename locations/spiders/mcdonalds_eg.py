from locations.spiders.mcdonalds_au import McDonaldsAUSpider


class McDonaldsEGSpider(McDonaldsAUSpider):
    name = "mcdonalds_eg"
    allowed_domains = ["mcdonalds.eg"]
    start_urls = ["https://mcdonalds.eg/Stotes"]
