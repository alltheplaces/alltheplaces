from locations.spiders.pep_zm import PepZMSpider


class PepMWSpider(PepZMSpider):
    name = "pep_mw"
    start_urls = ["https://www.pep.co.mw/api/stores.json"]
