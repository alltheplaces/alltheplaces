from locations.spiders.pep_zm import PepZMSpider


class PepMZSpider(PepZMSpider):
    name = "pep_mz"
    start_urls = ["https://www.pep.co.mz/api/stores.json"]
