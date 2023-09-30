import re

import scrapy

from locations.items import Feature


class LesliesPoolmartSpider(scrapy.Spider):
    name = "leslies_poolmart"
    item_attributes = {"brand": "Leslie's Poolmart", "brand_wikidata": "Q6530568"}
    allowed_domains = ["lesliespool.com"]
    start_urls = [
        "https://lesliespool.com/sitemap_2.xml",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath('//url/loc[contains(text(), "/location/")]/text()').extract()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        store_title = response.xpath("//h1/text()").extract_first()

        # Handle handful of empty pages
        if store_title:
            ref = re.search(r".*\s#?([0-9]*)", store_title).group(1)

            city_state_postal = response.xpath('//h5[@class="store-detail-address"]/span[3]/text()').extract_first()

            if city_state_postal:  # Get store details, otherwise pass if empty page
                city, state, zipcode = re.search(
                    r"^(.*),\s*([a-z]{2})\s*([0-9]{5}).*$",
                    city_state_postal.strip(),
                    re.IGNORECASE,
                ).groups()

                properties = {
                    "ref": ref,
                    "name": response.xpath('//h5[@class="store-detail-address"]/span[1]/text()').extract_first(),
                    "street_address": response.xpath(
                        '//h5[@class="store-detail-address"]/span[2]/text()'
                    ).extract_first(),
                    "city": city,
                    "state": state,
                    "postcode": zipcode,
                    "country": "US",
                    "lat": float(
                        response.xpath(
                            '//a[contains(@class, "select-store-button")]/@data-store-latitude'
                        ).extract_first()
                    ),
                    "lon": float(
                        response.xpath(
                            '//a[contains(@class, "select-store-button")]/@data-store-longitude'
                        ).extract_first()
                    ),
                    "phone": response.xpath('//h5[contains(@class, "store-detail-phone")]/text()').extract_first(),
                    "website": response.url,
                }

                yield Feature(**properties)
