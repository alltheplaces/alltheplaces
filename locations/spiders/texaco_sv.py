from locations.spiders.texaco_co import TexacoCOSpider


class TexacoSVSpider(TexacoCOSpider):
    name = "texaco_sv"
    start_urls = ["https://www.texacocontechron.com/sv/estaciones/"]
