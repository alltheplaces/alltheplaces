from locations.spiders.fressnapf_de import FressnapfDESpider


class FressnapfCHSpider(FressnapfDESpider):
    name = "fressnapf_ch"
    api_key = "fressnapfCH"
    website_format = "https://www.fressnapf.lu/stores/{}/"
