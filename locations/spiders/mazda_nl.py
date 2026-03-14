from locations.spiders.mazda_de import MazdaDESpider


class MazdaNLSpider(MazdaDESpider):
    name = "mazda_nl"
    allowed_domains = ["www.mazda.nl"]
