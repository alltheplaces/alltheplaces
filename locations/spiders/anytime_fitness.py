# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
import html


class AnytimeFitnessSpider(scrapy.Spider):
    name = "anytime_fitness"
    item_attributes = {"brand": "Anytime Fitness", "brand_wikidata": "Q4778364"}
    allowed_domains = ["www.anytimefitness.com"]

    def start_requests(self):
        url = "https://www.anytimefitness.com/wp-content/uploads/locations.json"
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        gyms = json.loads(response.text)

        for gym in gyms:
            yield GeojsonPointItem(
                lat=gym["latitude"],
                lon=gym["longitude"],
                addr_full=", ".join(
                    filter(
                        None, [gym["content"]["address"], gym["content"]["address2"]]
                    )
                ),
                city=gym["content"]["city"],
                phone=gym["content"]["phone"],
                state=gym["content"]["state_abbr"],
                postcode=gym["content"]["zip"],
                ref=gym["content"]["url"],
                country=gym["content"]["country"],
                name=html.unescape(gym["content"]["title"]),
                extras={"number": gym["content"]["number"]},
            )
