import json

from scrapy.spiders import SitemapSpider
from locations.items import GeojsonPointItem


class HungryHorseSpider(SitemapSpider):
    name = "hungry_horse"
    item_attributes = {"brand": "Hungry Horse", "brand_wikidata": "Q5943510"}
    allowed_domains = ["www.hungryhorse.co.uk"]
    sitemap_urls = ["https://www.hungryhorse.co.uk/xml-sitemap"]
    sitemap_rules = [
        (
            r"https://www.hungryhorse.co.uk/pubs/(west-[\w-]+)/([\w-]+)/$",
            "parse",
        ),
    ]
    download_delay = 0.5

    def sitemap_filter(self, entries):
        for entry in entries:
            if (
                entry["loc"]
                != "https://www.hungryhorse.co.uk/pubs/west-lothian/lime-kiln/"
            ):
                yield entry

    def parse(self, response):
        ld = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )
        if not ld.get("branchCode"):
            return
        properties = {
            "ref": ld["branchCode"],
            "website": response.request.url,
            "name": ld["name"],
            "phone": ld["telephone"],
            "opening_hours": "; ".join(ld["openingHours"]),
            "lat": ld["geo"]["latitude"],
            "lon": ld["geo"]["longitude"],
            "addr_full": ld["address"] + ", United Kingdom",
            "country": "GB",
        }

        yield GeojsonPointItem(**properties)
