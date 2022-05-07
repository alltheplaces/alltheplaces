import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.spiders import SitemapSpider

DAY_MAPPING = {
    "MONDAY": "Mo",
    "TUESDAY": "Tu",
    "WEDNESDAY": "We",
    "THURSDAY": "Th",
    "FRIDAY": "Fr",
    "SATURDAY": "Sa",
    "SUNDAY": "Su",
}


class TescoSpider(SitemapSpider):
    name = "tesco"
    item_attributes = {"brand": "Tesco", "brand_wikidata": "Q487494"}
    allowed_domains = ["www.tesco.com"]
    download_delay = 0.3
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0",
    }
    sitemap_urls = [
        "https://www.tesco.com/store-locator/sitemap.xml",
    ]
    sitemap_rules = [
        (
            "https:\/\/www\.tesco\.com\/store-locator\/([\w\-\.]+)\/([\d]+\/)?([\w\-\.\(\)]+)$",
            "parse_store",
        )
    ]

    def store_hours(self, store_hours):
        opening_hours = OpeningHours()
        store_hours = json.loads(store_hours)

        for day in store_hours:
            closed = day["isClosed"]
            if not closed:
                opening_hours.add_range(
                    day=DAY_MAPPING[day["day"]],
                    open_time=str(day["intervals"][0]["start"]).zfill(4),
                    close_time=str(day["intervals"][0]["end"]).zfill(4),
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        store_details = response.xpath(
            '//script[@type="application/json"][@id="storeData"]/text()'
        ).extract_first()
        if store_details:
            store_data = json.loads(store_details)
            ref = store_data["store"]
            addr_1 = response.xpath(
                '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-line1"]/text()'
            ).extract_first()
            addr_2 = response.xpath(
                '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-line2"]/text()'
            ).extract_first()
            if addr_2:
                addr_full = ", ".join([addr_1.strip(), addr_2.strip()])
            else:
                addr_full = addr_1

            properties = {
                "ref": ref,
                "name": response.xpath(
                    '//h1[@itemprop="name"]/descendant-or-self::*/text()'
                ).get(),
                "street_address": addr_full,
                "city": response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-city"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-field Address-postalCode"]/text()'
                ).extract_first(),
                "country": "GB",
                "lat": response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-coordinates"]/meta[@itemprop="latitude"]/@content'
                ).extract_first(),
                "lon": response.xpath(
                    '//div[@class="Core-infoWrapper"]//span[@class="Address-coordinates"]/meta[@itemprop="longitude"]/@content'
                ).extract_first(),
                "phone": "+44 "
                + response.xpath(
                    '//span[@itemprop="telephone"]/text()'
                ).extract_first()[1:],
                "website": response.url,
            }

            hours = response.xpath(
                '//div[@class="Core-infoWrapper"]//@data-days'
            ).extract_first()
            if hours:
                properties["opening_hours"] = self.store_hours(hours)

            if store_data["storeformat"] == "Express":
                properties["brand"] = "Tesco Express"
                properties["brand_wikidata"] = "Q98456772"
            elif store_data["storeformat"] == "Superstore":
                properties["brand"] = "Tesco Superstore"
                properties["brand_wikidata"] = "Q487494"
            elif store_data["storeformat"] == "Extra":
                properties["brand"] = "Tesco Extra"
                properties["brand_wikidata"] = "Q25172225"

            yield GeojsonPointItem(**properties)
