from locations.spiders.zambrero_au import ZambreroAUSpider


class ZambreroUSSpider(ZambreroAUSpider):
    name = "zambrero_us"
    allowed_domains = ["www.zambrero.com"]
