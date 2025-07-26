from locations.spiders.mazda_de import MazdaDESpider


class MazdaADFRSpider(MazdaDESpider):
    name = "mazda_ad_fr"
    allowed_domains = ["www.mazda.fr"]
