import re

import scrapy

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsILSpider(scrapy.Spider):
    name = "mcdonalds_il"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.co.il"]
    start_urls = ("https://www.mcdonalds.co.il/%D7%90%D7%99%D7%AA%D7%95%D7%A8_%D7%9E%D7%A1%D7%A2%D7%93%D7%94",)

    # TODO: Does have hours but the days are not in english and the function does not work. Hence its deletion

    def parse_ref(self, data):
        match = re.search(r"store_id=(.*\d)", data)
        ref = match.groups()[0]
        return ref

    def parse_name(self, name):
        name = name.xpath("//h2[@class='mod_geo_location_store_title']/text()").extract_first()
        return name.strip()

    def parse_latlon(self, data, store_id):
        lat = lng = ""
        lat = data.xpath(f'//div[@class="mod_geo_location_store store_id_{store_id}"]/@lat').extract_first()
        lng = data.xpath(f'//div[@class="mod_geo_location_store store_id_{store_id}"]/@lng').extract_first()
        return lat, lng

    def parse_phone(self, phone):
        phone = phone.xpath('//div[@class="mod_geo_location_store_phone"]/span/a/text()').extract_first()
        if not phone:
            return ""
        return phone.strip()

    def parse_address(self, address):
        address = address.xpath("//div[@class='mod_geo_location_store_adrress']/h3[not(@class)]/text()").extract_first()
        return address.strip()

    def parse_store(self, response, store_id):
        name = self.parse_name(response)
        address = self.parse_address(response)
        phone = self.parse_phone(response)
        lat, lon = self.parse_latlon(response, store_id)
        properties = {
            "ref": response.meta["ref"],
            "phone": phone,
            "lon": lon,
            "lat": lat,
            "name": name,
            "addr_full": address,
        }

        yield Feature(**properties)

    def parse(self, response):
        stores = response.xpath('//div[@class="mod_geo_location_store_link"]/span/a/@href').extract()
        for store in stores:
            ref = self.parse_ref(store)
            yield scrapy.Request(
                "https:" + store, meta={"ref": ref}, callback=self.parse_store, cb_kwargs={"store_id": ref}
            )
