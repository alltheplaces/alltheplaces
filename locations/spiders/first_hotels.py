import json

import scrapy

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FirstHotelsSpider(StructuredDataSpider):
    name = "first_hotels"
    item_attributes = {"brand": "First Hotels", "brand_wikidata": "Q11969007"}
    start_urls = ["https://www.firsthotels.com/general-info/about-first-hotels/map-of-hotels/"]

    def parse(self, response):
        hotels = json.loads(response.xpath('//*[@class="allhotels"]/div/@data-pois').get())
        for hotel in hotels:
            yield scrapy.Request(url="https://www.firsthotels.com" + hotel["url"], callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        coords = ld_data["hasMap"].split("@")[1]
        item["name"] = item["name"].strip()
        item["lat"] = coords.split(",")[0]
        item["lon"] = coords.split(",")[1]

        for alt in response.xpath('//link[@rel="alternate"][@hreflang]'):
            item["extras"]["website:{}".format(alt.xpath("@hreflang").get())] = alt.xpath("@href").get()

        apply_category(Categories.HOTEL, item)
        yield item
