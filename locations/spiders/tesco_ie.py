from locations.spiders.tesco_gb import TescoGBSpider


class TescoIESpider(TescoGBSpider):
    name = "tesco_ie"
    sitemap_urls = ["https://www.tesco.ie/store-locator/sitemap.xml"]
