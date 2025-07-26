from locations.spiders.mazda_de import MazdaDESpider


class MazdaSKSpider(MazdaDESpider):
    name = "mazda_sk"
    allowed_domains = ["www.mazda.sk"]
