from locations.spiders.virgin_active_sg import VirginActiveSGSpider


class VirginActiveAUSpider(VirginActiveSGSpider):
    name = "virgin_active_au"
    start_urls = ["https://www.virginactive.com.au/locations"]
