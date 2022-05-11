import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class CurrysSpider(SitemapSpider):
    name = "currys"
    item_attributes = {"brand": "currys", "brand_wikidata": "Q3246464"}
    allowed_domains = ["www.currys.co.uk"]
    sitemap_urls = ["https://www.currys.co.uk/sitemap-stores.xml"]

    def parse(self, response, **kwargs):
        ld = json.loads(response.xpath('//script[@type="application/ld+json"]').get())

        oh = OpeningHours()
        for rule in ld["openingHoursSpecification"]:
            for day in rule["dayOfWeek"]:
                oh.add_range(day[:2], rule["opens"], rule["closes"])

        yield Feature(
            lat=response.xpath('//input[@class="storeDetailLat"]/@value').get(),
            lon=response.xpath('//input[@class="storeDetailLong"]/@value').get(),
            name=response.xpath('//h1[@class="store-information-page-title"]/text()').get(),
            addr_full=response.xpath('//span[@class="storeinfo-addres storeinfowidth"]/text()').get()
            + ", United Kingdom",
            street_address=ld["address"]["streetAddress"],
            postcode=ld["address"]["postalCode"],
            country="GB",
            website=response.request.url,
            opening_hours=oh.as_opening_hours(),
            ref=ld["@id"],
        )
