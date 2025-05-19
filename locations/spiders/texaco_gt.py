from locations.spiders.texaco_co import TexacoCOSpider


class TexacoGTSpider(TexacoCOSpider):
    name = "texaco_gt"
    start_urls = ["https://www.texacocontechron.com/gt/estaciones/"]
