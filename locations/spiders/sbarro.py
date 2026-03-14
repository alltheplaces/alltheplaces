import json

import scrapy

from locations.items import Feature


class SbarroSpider(scrapy.Spider):
    name = "sbarro"
    item_attributes = {"brand": "Sbarro", "brand_wikidata": "Q2589409"}
    allowed_domains = ["sbarro.com"]
    start_urls = ["https://sbarro.com/locations/?user_search=78749&radius=50000&count=5000"]

    def parse_store(self, response):
        try:
            data = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "PostalAddress")]/text()'
                ).extract_first(),
                strict=False,
            )
            properties = {
                "ref": response.meta["ref"],
                "branch": response.xpath('//*[@class="location-name "]/text()').extract_first(),
                "street_address": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "lat": response.meta["lat"],
                "lon": response.meta["lon"],
                "website": response.url,
            }

            yield Feature(**properties)
        except:
            pass

    def parse(self, response):
        store_urls = response.xpath('//*[@class="location-name "]/a/@href').extract()
        ids = response.xpath('//*[@class="locations-result"]/@id').extract()
        lats = response.xpath('//*[@class="locations-result"]/@data-latitude').extract()
        longs = response.xpath('//*[@class="locations-result"]/@data-longitude').extract()

        for store_url, id, lat, long in zip(store_urls, ids, lats, longs):
            store_url = "https://sbarro.com" + store_url + "/"
            yield scrapy.Request(
                response.urljoin(store_url),
                callback=self.parse_store,
                meta={"lat": lat, "lon": long, "ref": id},
            )
