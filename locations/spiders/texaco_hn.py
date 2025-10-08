from locations.spiders.texaco_co import TexacoCOSpider


class TexacoHNSpider(TexacoCOSpider):
    name = "texaco_hn"
    start_urls = ["https://www.texacocontechron.com/hn/estaciones/"]
