import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class AthletaSpider(scrapy.Spider):
    name = "athleta"
    item_attributes = {"brand": "Athleta", "brand_wikidata": "Q105722424"}
    athleta_url = "https://athleta.gap.com"
    athleta_store_url = "https://athleta.gap.com/stores"
    start_urls = (athleta_store_url,)

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        data = response.xpath('//a[@class="ga-link"]/@href').extract()
        for store in data:
            yield scrapy.Request(
                self.athleta_url + store, callback=self.parse_list_store
            )

    def parse_list_store(self, response):
        data = response.xpath('//a[@class="ga-link"]/@href').extract()
        for store in data:
            yield scrapy.Request(self.athleta_url + store, callback=self.parse_store)

    def parse_store(self, response):
        data = self.find_between(response.text, "$config.defaultListData = '", ";")
        data = (
            data.replace("/", "")
            .replace("\\", "")
            .replace("'", "")
            .replace('"{"', '{"')
            .replace('"}"', '"}')
            .replace('}"', "}")
        )
        json_data = json.loads(data)[0]

        days = json_data["hours_sets:primary"]["days"]
        oh = OpeningHours()
        for key, value in days.items():
            if "open" in value[0]:
                oh.add_range(key, value[0]["open"], value[0]["close"])

        properties = {
            "phone": json_data["local_phone"],
            "ref": json_data["fid"],
            "name": json_data["location_name"],
            "opening_hours": oh.as_opening_hours(),
            "addr_full": json_data["address_1"],
            "housenumber": json_data["address_1"].strip().split()[0],
            "street": json_data["address_1"]
            .replace(json_data["address_1"].strip().split()[0], "")
            .strip(),
            "city": json_data["city"],
            "state": json_data["region"],
            "postcode": json_data["post_code"],
            "country": json_data["country"],
            "website": self.athleta_store_url
            + "/"
            + json_data["region"].lower()
            + "/"
            + json_data["city"].lower()
            + "/"
            + json_data["url_search_term"],
            "lat": json_data["lat"],
            "lon": json_data["lng"],
        }

        yield GeojsonPointItem(**properties)
