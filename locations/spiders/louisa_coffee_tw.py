import scrapy

from locations.items import Feature


class LouisaCoffeeTWSpider(scrapy.Spider):
    name = "louisa_coffee_tw"
    item_attributes = {"brand": "Louisa Coffee", "brand_wikidata": "Q96390921"}
    start_urls = ["https://www.louisacoffee.co/visit_result?data[county]="]

    def parse(self, response):
        location_hrefs = response.xpath('//a[contains(@class, "marker")]')
        for location_href in location_hrefs:
            properties = {
                "name": location_href.xpath("@rel-store-name").extract_first(),
                "addr_full": location_href.xpath("@rel-store-address").extract_first(),
                "ref": location_href.xpath(
                    "@rel-store-name"
                ).extract_first(),  # using the name in lieu of an ID of any kind
                "lon": location_href.xpath("@rel-store-lng").extract_first(),
                "lat": location_href.xpath("@rel-store-lat").extract_first(),
                "phone": location_href.xpath('.//ancestor::*[@class="row"]//*[contains(text(),"電話")]/text()')
                .extract_first()
                .replace("電話/", ""),
            }

            yield Feature(**properties)
