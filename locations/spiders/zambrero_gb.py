from locations.spiders.zambrero_au import ZambreroAUSpider


class ZambreroGBSpider(ZambreroAUSpider):
    name = "zambrero_gb"
    allowed_domains = ["www.zambrero.co.uk"]
