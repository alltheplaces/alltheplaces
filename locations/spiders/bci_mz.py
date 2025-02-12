from chompjs import parse_js_object
from scrapy import Selector, Spider
from scrapy.http import Request

from locations.categories import Categories
from locations.items import Feature


class BciMZSpider(Spider):
    name = "bci_mz"
    allowed_domains = ["www.bci.co.mz"]
    start_urls = ["https://www.bci.co.mz/onde-estamos/"]
    item_attributes = {"brand": "BCI", "brand_wikidata": "Q9645132", "extras": Categories.BANK.value}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def parse(self, response):
        for province in response.xpath('.//div[@id="provincias-menu"]/a'):
            province_name = province.xpath("text()").get()
            province_id = province.xpath("@data-value").get()
            yield Request(
                url=f"https://www.bci.co.mz/mapaagenciasabado22/?prov={province_id}&segmento=universal&saturday=0",
                meta={"province": province_name},
                callback=self.parse_province,
            )

    def parse_province(self, response):
        markers = response.xpath('.//script[contains(text(), "minhaVariavel.addMarker")]/text()').getall()
        for marker in markers:
            location = parse_js_object(marker, loader_kwargs={"strict": False})
            item = Feature()
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["branch"] = location["title"]
            item["state"] = response.meta["province"]
            info = Selector(text=location["infoWindow"]["content"])
            item["phone"] = info.xpath('//span[contains(text(), "Tel:")]/../text()').get()
            item["email"] = info.xpath('//span[contains(text(), "E-mail:")]/../text()').get()
            yield item
