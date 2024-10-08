import re

import scrapy

from locations.structured_data_spider import StructuredDataSpider


class PkEquipmentSpider(StructuredDataSpider):
    name = "pk_equipment"
    item_attributes = {"brand": "P&K Equipment", "extras": {"shop": "tractor"}}
    allowed_domains = ["pkequipment.com"]
    start_urls = ("https://www.pkequipment.com/about-us/locations/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="li-text"]/h2/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        mapdata = response.xpath('//div[@class="clearfix map_equipment"]/script[2]').extract_first()
        lat = re.search(r'(?:lat":)(-?\d+\.\d+),.*(?:long":)(-?\d*.\d*)', mapdata).group(1)
        lon = re.search(r'(?:lat":)(-?\d+\.\d+),.*(?:long":)(-?\d*.\d*)', mapdata).group(2)
        item["ref"] = ref
        item["lat"] = float(lat)
        item["lon"] = float(lon)

        yield item
