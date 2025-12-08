from locations.spiders.pep_zm import PepZMSpider


class PepAOSpider(PepZMSpider):
    name = "pep_ao"
    start_urls = ["https://www.pep.co.ao/api/stores.json"]
