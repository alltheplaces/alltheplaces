from locations.spiders.mazda_de import MazdaDESpider


class MazdaLUSpider(MazdaDESpider):
    name = "mazda_lu"
    allowed_domains = ["www.mazda.lu"]
