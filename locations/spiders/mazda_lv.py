from locations.spiders.mazda_fi import MazdaFISpider


class MazdaLVSpider(MazdaFISpider):
    name = "mazda_lv"
    start_urls = ["https://www.mazda.lv/atrast-parstavi"]
    country = "LV"
