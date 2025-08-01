from locations.spiders.mazda_de import MazdaDESpider


class MazdaTRSpider(MazdaDESpider):
    name = "mazda_tr"
    allowed_domains = ["www.mazda.com.tr"]
