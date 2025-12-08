from locations.spiders.fressnapf_de import FressnapfDESpider


class FressnapfLUSpider(FressnapfDESpider):
    name = "fressnapf_lu"
    api_key = "fressnapfLU"
    website_format = "https://www.fressnapf.lu/stores/fressnapf-walferdange/"
