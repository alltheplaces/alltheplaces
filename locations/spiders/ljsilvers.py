# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class LjsilversSpider(scrapy.Spider):
    name = "ljsilvers"
    item_attributes = {"brand": "Long John Silver's", "brand_wikidata": "Q1535221"}
    allowed_domains = ["ljsilvers.com"]
    start_urls = (
        "https://viewer.blipstar.com/searchdbnew?uid=2483677&lat=45&lng=-103&value=10000",
    )

    def parse(self, response):
        for row in response.json():
            if row.keys() == {"fulltotal", "total", "units"}:
                continue
            addr = scrapy.Selector(text=row["a"])
            properties = {
                "name": row["n"],
                "ref": row["bpid"],
                "lat": row["lat"],
                "lon": row["lng"],
                "addr_full": addr.xpath("//p/text()").extract_first(),
                "city": addr.css(".storecity ::text").extract_first(),
                "state": addr.css(".storestate ::text").extract_first(),
                "postcode": addr.css(".storepostalcode ::text").extract_first(),
                "country": row["c"],
                "phone": row["p"],
            }
            yield GeojsonPointItem(**properties)
