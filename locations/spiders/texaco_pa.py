from locations.spiders.texaco_co import TexacoCOSpider


class TexacoPASpider(TexacoCOSpider):
    name = "texaco_pa"
    start_urls = ["https://www.texacocontechron.com/pa/estaciones/"]
