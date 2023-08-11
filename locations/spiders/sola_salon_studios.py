from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class SolaSalonStudiosSpider(SitemapSpider):
    name = "sola_salon_studios"
    item_attributes = {"brand": "Sola Salon Studios", "brand_wikidata": "Q64337426"}
    allowed_domains = ["www.solasalonstudios.com"]
    sitemap_urls = ["https://www.solasalonstudios.com/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[\w\-]+", "parse")]

    def parse(self, response):
        location_js = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        location = parse_js_object(location_js)["props"]["pageProps"]["locationSEODetails"]["data"]
        item = DictParser.parse(location)
        item["ref"] = response.url
        item["street_address"] = ", ".join(filter(None, [location["address_1"], location["address_2"]]))
        item["website"] = response.url
        yield item
