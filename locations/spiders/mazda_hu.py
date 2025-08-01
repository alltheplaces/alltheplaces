from locations.spiders.mazda_de import MazdaDESpider


class MazdaHUSpider(MazdaDESpider):
    name = "mazda_hu"
    allowed_domains = ["www.mazda.hu"]
