from locations.spiders.mazda_de import MazdaDESpider


class MazdaDKFOISSpider(MazdaDESpider):
    name = "mazda_dk_fo_is"
    allowed_domains = ["www.mazda.dk"]
