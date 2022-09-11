import datetime
import json

from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PapaMurphysSpider(SitemapSpider):
    name = "papamurphys"
    item_attributes = {"brand": "Papa Murphy's", "brand_wikidata": "Q7132349"}
    allowed_domains = ["papamurphys.com"]
    download_delay = 0.5
    sitemap_urls = ["https://locations.papamurphys.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"^https://locations.papamurphys.com/[^/]+/[^/]+/[^/]+?",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        properties = {
            "street_address": response.xpath('//*[@itemprop="streetAddress"]/@content').extract_first(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').extract_first(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            "country": response.xpath('//*[@itemprop="address"]/@data-country').extract_first(),
            "ref": response.url,
            "website": response.url,
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath('//*[@itemprop="longitude"]/@content').extract_first(),
        }

        hours = json.loads(
            response.xpath('//script[@class="js-hours-config"]/text()').get()
        )
        opening_hours = OpeningHours()
        for row in hours["hours"]:
            day = row["day"][:2].capitalize()
            for i in row["intervals"]:
                start_hour, start_minute = divmod(i["start"], 100)
                end_hour, end_minute = divmod(i["end"], 100)
                start_time = f"{start_hour:02}:{start_minute:02}"
                end_time = f"{end_hour:02}:{end_minute:02}"
                opening_hours.add_range(day, start_time, end_time)

        if hours:
            properties["opening_hours"] = opening_hours.as_opening_hours()

        yield GeojsonPointItem(**properties)
