from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FI, OpeningHours
from locations.items import Feature


class SpecsaversFISpider(CrawlSpider):
    name = "specsavers_fi"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.fi/liikehaku/kaikki-liikkeemme"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.specsavers\.fi\/liikehaku\/(?!kaikki-liikkeemme)((?!<\/).+)$"),
            callback="parse_store",
        )
    ]

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//div[contains(@class, "js-yext-info")]/@data-yext-url').get().split("?", 1)[0],
            "name": response.xpath('//h1[contains(@class, "store-header--title")]/text()').get().strip(),
            "lat": response.xpath("//div/@data-store-geo-loc-lat").get().strip(),
            "lon": response.xpath("//div/@data-store-geo-loc-lng").get().strip(),
            "addr_full": " ".join(
                (" ".join(response.xpath('//div[contains(@class, "store")]/p[1]/span/text()').getall())).split()
            ),
            "postcode": response.xpath('//div[contains(@class, "store")]/p[1]/span[@itemprop="postalCode"]/text()')
            .get()
            .strip(),
            "city": response.xpath('//div[contains(@class, "store")]/p[1]/span[@itemprop="addressRegion"]/text()')
            .get()
            .strip(),
            "phone": response.xpath('//span[contains(@class, "contact--store-telephone--text")]/text()').get().strip(),
            "website": response.url,
        }

        oh = OpeningHours()
        hours_raw = (
            (" ".join(response.xpath('//tr[@itemprop="openingHours"]/@content').getall()))
            .replace("Suljettu", "0:00 - 0:00")
            .replace(" - ", " ")
            .split()
        )
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[1] == "0:00" and day[2] == "0:00":
                continue
            oh.add_range(DAYS_FI[day[0].title()], day[1].upper(), day[2].upper())
        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
