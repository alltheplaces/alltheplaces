import json

import scrapy

from locations.linked_data_parser import LinkedDataParser


class Take5OilChangeSpider(scrapy.Spider):
    name = "take5"
    item_attributes = {
        "brand": "Take 5 Oil Change",
        "brand_wikidata": "Q112359190",
    }
    allowed_domains = ["www.take5oilchange.com"]
    start_urls = [
        "https://www.take5oilchange.com/locations/",
    ]

    def parse(self, response):
        script = response.xpath('//script/text()[contains(.,"var CITIES =")]').get()
        start = script.index("{", script.index("var CITIES ="))
        data = json.decoder.JSONDecoder().raw_decode(script, start)[0]
        for state, cities in data.items():
            for city in cities:
                url = f"https://www.take5oilchange.com/locations/{state}/{city['citySlug']}/"
                yield scrapy.Request(url, callback=self.parse_city)

    def parse_city(self, response):
        locations = response.xpath('//div[@id="data-json-locations"]/@data-json').get()
        if locations is not None:
            for row in json.loads(locations):
                yield scrapy.Request(
                    f'https://www.take5oilchange.com/locations/{row["storeUrl"]}',
                    callback=self.parse_city,
                )

        ld = LinkedDataParser.find_linked_data(response, "Service")
        if ld is not None:
            item = LinkedDataParser.parse_ld(ld["provider"])
            item["ref"] = response.xpath("//@data-storeid").get()
            item["website"] = response.url
            yield item
