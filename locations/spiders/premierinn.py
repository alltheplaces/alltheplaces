import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

BASE_URL = "https://www.premierinn.com/gb/en/"


class PremierInnSpider(scrapy.spiders.SitemapSpider):
    name = "premierinn"
    item_attributes = {"brand": "Premier Inn", "brand_wikidata": "Q2108626"}
    allowed_domains = ["premierinn.com"]
    download_delay = 0.5
    sitemap_urls = ("https://www.premierinn.com/sitemap-english.xml",)
    sitemap_rules = [
        (
            "gb/en/hotels/[^/]+/[^/]+/[^/]+/[^/]+.html",
            "parse_location",
        ),
    ]

    def parse_location(self, response):
        if response.xpath('//section[@class="seo-hotel-listings"]'):
            # Page with multiple hotels that has the same URL format as single-hotel pages
            return

        properties = {
            "ref": re.search(r"([^/]+/[^/]+/[^/]+/[^/]+).html$", response.url).group(1),
            "name": response.xpath('//meta[@itemprop="name"]/@content')
            .extract_first()
            .strip(),
            "street_address": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": " ".join(
                filter(
                    None,
                    response.xpath(
                        '//span[@itemprop="addressLocality"]/text()'
                    ).extract(),
                )
            ),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '//span[@data-ng-bind-html="$ctrl.hotelPhoneNumber"]/text()'
            ).extract_first(),
            "country": response.xpath(
                '//ol[@class="nav breadcrumb--path"]/li[3]/a/text()'
            ).extract_first(),
            "lat": response.xpath(
                '//meta[@itemprop="latitude"]/@content'
            ).extract_first(),
            "lon": response.xpath(
                '//meta[@itemprop="longitude"]/@content'
            ).extract_first(),
            "image": response.urljoin(
                response.xpath(
                    '//a[@id="gallery-item-single"]/img/@src'
                ).extract_first()
            ),
            "phone": response.xpath(
                "//*[@hotel-phone-number]/@hotel-phone-number"
            ).extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
