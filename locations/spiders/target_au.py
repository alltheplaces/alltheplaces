# -*- coding: utf-8 -*-
import scrapy
import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class TargetAUSpider(scrapy.Spider):
    name = "target_au"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q7685854"}
    allowed_domains = ["target.com.au"]
    start_urls = ["https://www.target.com.au/store-finder"]
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; CrOS aarch64 14324.72.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.91 Safari/537.36",
    }
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": headers,
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"
        },
    }

    def parse(self, response):
        for href in response.xpath('//*[@class="store-states"]//@href').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url, callback=self.parse_state)

    def parse_state(self, response):
        data = json.loads(
            response.xpath('//script[@id="store-json-data"]/text()').get()
        )
        for row in data["locations"]:
            body = scrapy.Selector(text=row["content"])
            href = body.xpath("//@href").get()
            properties = {
                "ref": href.rsplit("/", 1)[-1],
                "name": row["name"],
                "lat": row["lat"],
                "lon": row["lng"],
                "addr_full": " ".join(
                    s.strip()
                    for s in body.xpath(
                        '//*[@itemprop="streetAddress"]//text()'
                    ).extract()
                ),
                "city": body.xpath('//*[@itemprop="addressLocality"]/text()').get(),
                "state": body.xpath('//*[@itemprop="addressRegion"]/text()').get(),
                "postcode": body.xpath('//*[@itemprop="postalCode"]/text()').get(),
                "phone": body.xpath("//p[last()-1]/text()").get(),
                "website": response.urljoin(href),
            }
            yield GeojsonPointItem(**properties)
