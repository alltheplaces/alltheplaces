from locations.spiders.fressnapf_de import FressnapfDESpider


class FressnapfATSpider(FressnapfDESpider):
    name = "fressnapf_at"
    api_key = "fressnapfAT"
    website_format = "https://www.fressnapf.at/stores/{}/"
