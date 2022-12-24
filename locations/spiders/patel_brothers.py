# # -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class PatelBrothersSpider(scrapy.Spider):
    name = "patel_brothers"
    item_attributes = {
        "brand": "Patel Brothers",
        "brand_wikidata": "Q55641396",
    }
    start_urls = ["https://www.patelbros.com/wp-content/plugins/superstorefinder-wp/ssf-wp-xml.php"]

    def parse(self, response):
        items = response.xpath("//store/item")
        for item in items:
            properties = {
                "lat": item.xpath("latitude//text()").extract_first(),
                "lon": item.xpath("longitude//text()").extract_first(),
                "phone": item.xpath("telephone//text()").extract_first(),
                "street_address": item.xpath("address//text()").extract_first().split("<br />")[0],
                "addr_full": item.xpath("address//text()").extract_first().replace("<br />", ","),
                "email": item.xpath("email//text()").extract_first(),
                "website": item.xpath("exturl//text()").extract_first(),
                "ref": item.xpath("exturl//text()").extract_first(),
            }
            yield GeojsonPointItem(**properties)
