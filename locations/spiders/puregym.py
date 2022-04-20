import json

from urllib.parse import urlparse, parse_qsl
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
            "website": response.request.url,
            "name": ld["name"],
            "phone": ld["telephone"],
            "street": ld["location"]["address"]["streetAddress"],
            "city": ld["location"]["address"]["addressLocality"],
            "postcode": ld["location"]["address"]["postalCode"],
            "country": "GB",
            "extras": {
                "email": ld["email"],
            },
        }

        properties["addr_full"] = ", ".join(
            (
                properties["street"],
                properties["city"],
                properties["postcode"],
                properties["country"],
            )
        )
        properties["ref"] = response.xpath('//meta[@itemprop="gymId"]/@content').get()

        maplink = urlparse(
            response.xpath(
                '//*[@class="gym-map static-map"]/img[@id="view-location-bottom_map"]/@src'
            ).get()
        )
        query = dict(parse_qsl(maplink.query))

        properties["lon"] = query["center"].split(",")[1]
        properties["lat"] = query["center"].split(",")[0]

        yield GeojsonPointItem(**properties)
