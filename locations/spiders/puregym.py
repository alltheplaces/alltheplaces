import json

from locations.google_url import url_to_coords
from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class PureGymSpider(SitemapSpider):
    name = "puregym"
    item_attributes = {"brand": "PureGym", "brand_wikidata": "Q18345898"}
    allowed_domains = ["www.puregym.com"]
    sitemap_urls = ["https://www.puregym.com/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/www\.puregym\.com\/gyms\/([\w-]+)\/$",
            "parse_location",
        ),
    ]

    def parse_location(self, response):
        page_title = response.xpath("/html/head/title/text()").get().lower()
        if "coming soon" in page_title:
            return

        ld = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )

        properties = {
            "ref": response.xpath('//meta[@itemprop="gymId"]/@content').get(),
            "website": response.request.url,
            "name": ld["name"],
            "phone": ld["telephone"],
            "street_address": ld["location"]["address"]["streetAddress"],
            "city": ld["location"]["address"]["addressLocality"],
            "postcode": ld["location"]["address"]["postalCode"],
            "country": "GB",
            "addr_full": ", ".join(
                filter(
                    None,
                    (
                        ld["location"]["address"]["streetAddress"],
                        ld["location"]["address"]["addressLocality"],
                        ld["location"]["address"]["postalCode"],
                        "United Kingdom",
                    ),
                )
            ),
            "extras": {
                "email": ld["email"],
            },
        }

        properties["lat"], properties["lon"] = url_to_coords(
            response.xpath(
                '//*[@class="gym-map static-map"]/img[@id="view-location-bottom_map"]/@src'
            ).get()
        )

        yield GeojsonPointItem(**properties)
