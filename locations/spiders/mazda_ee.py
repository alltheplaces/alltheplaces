from locations.spiders.mazda_fi import MazdaFISpider


class MazdaEESpider(MazdaFISpider):
    name = "mazda_ee"
    start_urls = ["https://www.mazda.ee/edasimuujad"]
    country = "EE"
