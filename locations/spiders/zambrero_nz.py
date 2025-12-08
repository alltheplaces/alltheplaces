from locations.spiders.zambrero_au import ZambreroAUSpider


class ZambreroNZSpider(ZambreroAUSpider):
    name = "zambrero_nz"
    allowed_domains = ["www.zambrero.co.nz"]
