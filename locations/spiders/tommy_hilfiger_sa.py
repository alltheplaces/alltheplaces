from locations.spiders.tommy_hilfiger_ae import TommyHilfigerAESpider


class TommyHilfigerSASpider(TommyHilfigerAESpider):
    name = "tommy_hilfiger_sa"
    allowed_domains = ["en-sa.tommy.com"]
    start_urls = ["https://en-sa.tommy.com/storelocator"]
