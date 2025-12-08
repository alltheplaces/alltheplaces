from locations.spiders.zambrero_au import ZambreroAUSpider


class ZambreroIESpider(ZambreroAUSpider):
    name = "zambrero_ie"
    allowed_domains = ["www.zambrero.ie"]
