from locations.spiders.mazda_de import MazdaDESpider


class MazdaCHSpider(MazdaDESpider):
    name = "mazda_ch"
    allowed_domains = ["de.mazda.ch"]
