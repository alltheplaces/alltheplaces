import json

from scrapy import Request

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TommyBahamaSpider(StructuredDataSpider):
    name = "tommy_bahama"
    item_attributes = {"brand": "Tommy Bahama", "brand_wikidata": "Q3531299"}
    start_urls = ["https://www.tommybahama.com/store-finder"]
    search_for_email = False
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        script = response.xpath("//div[@tbr-all-stores]/following-sibling::script/text()").get()
        all_stores_data = json.loads(script[script.find("[") : script.rfind("]") + 1])
        for store in all_stores_data:
            yield Request(
                response.urljoin(store["url"]),
                callback=self.parse_island if store["storeType"] == "ISLAND" else self.parse_sd,
            )

    def parse_island(self, response):
        item = Feature()
        item["website"] = response.url
        item["lat"] = response.xpath("//@location-latitude").get()
        item["lon"] = response.xpath("//@location-longitude").get()
        item["branch"] = item["ref"] = response.xpath("//@location-name").get()
        item["street_address"] = response.xpath("//@location-address").get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath("//@location-city-state-zip").get()]
        )
        item["extras"] = Categories.RESTAURANT.value

        oh = OpeningHours()
        for row in response.css(".hours tr"):
            oh.add_ranges_from_string(" ".join(row.xpath("*/text()").getall()))
        item["opening_hours"] = oh

        yield item

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item["ref"] = item.pop("name")

        oh = OpeningHours()
        for day, times in zip(
            response.css(".store-hours-columns-left div"), response.css(".store-hours-columns-right div")
        ):
            oh.add_ranges_from_string(f"{day.xpath('text()').get()} {times.xpath('text()').get()}")
        item["opening_hours"] = oh

        yield item
