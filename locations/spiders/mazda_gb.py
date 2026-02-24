from locations.spiders.mazda_de import MazdaDESpider


class MazdaGBSpider(MazdaDESpider):
    name = "mazda_gb"
    allowed_domains = ["www.mazda.co.uk"]
