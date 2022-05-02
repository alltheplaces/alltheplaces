import scrapy

from locations.items import GeojsonPointItem
from urllib.parse import urljoin


class FrankieAndBennysSpider(scrapy.Spider):
    name = "frankie_and_bennys"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    allowed_domains = ["www.frankieandbennys.com"]
    start_urls = ["https://www.frankieandbennys.com/restaurants/index.html"]
    download_delay = 1

    def parse(self, response):
        root = response.xpath(
            '//*[@itemscope][@itemtype="http://schema.org/Restaurant"]'
        )
        if root:
            properties = {
                "lat": root.xpath(
                    './/*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="latitude"]/@content'
                ).get(),
                "lon": root.xpath(
                    './/*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="longitude"]/@content'
                ).get(),
                "ref": response.request.url,
                "website": response.request.url,
                "name": root.xpath('.//*[@itemprop="name"]/text()').get(),
                "phone": root.xpath('.//*[@itemprop="telephone"]/text()').get(),
                "opening_hours": "; ".join(
                    root.xpath('.//*[@itemprop="openingHours"]/@content').getall()
                ),
                "street_address": root.xpath(
                    './/address[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//meta[@itemprop="streetAddress"]/@content'
                ).get(),
                "city": root.xpath(
                    './/address[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//meta[@itemprop="addressLocality"]/@content'
                ).get(),
                "postcode": root.xpath(
                    './/address[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//span[@itemprop="postalCode"]/text()'
                ).get(),
                "country": root.xpath(
                    './/address[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//abbr[@itemprop="addressCountry"]/text()'
                ).get(),
                "extras": {},
            }
            extra_features = root.xpath(
                './/span[@itemprop="amenityFeature"]/text()'
            ).getall()
            for feature in extra_features:
                if feature.lower() == "disabled access":
                    properties["extras"]["wheelchair"] = "yes"

            properties["phone"] = "+44 " + properties["phone"][1:]
            properties["addr_full"] = ", ".join(
                filter(
                    None,
                    (
                        properties["street_address"],
                        properties["city"],
                        properties["postcode"],
                        "United Kingdom",
                    ),
                )
            )

            yield GeojsonPointItem(**properties)
        else:
            links = response.xpath('//*[@class="Directory-listLink"]')
            if not links:
                links = response.xpath('//*[@class="Teaser-titleLink"]')
            for link in links:
                yield scrapy.Request(urljoin(response.url, link.xpath("./@href").get()))
