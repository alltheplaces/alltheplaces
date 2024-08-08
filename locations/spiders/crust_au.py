from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CrustAUSpider(Spider):
    name = "crust_au"
    item_attributes = {"brand": "Crust", "brand_wikidata": "Q100792715"}
    allowed_domains = ["www.crust.com.au"]
    start_urls = ["https://www.crust.com.au/stores/stores_for_map_markers.json?catering_active=false"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location["location"].split(",", 1)
            item.pop("addr_full", None)
            item["street_address"] = clean_address([location["address"], location["address2"]])
            item["postcode"] = str(item.get("postcode", ""))
            yield Request(
                url="https://www.crust.com.au/stores/{}/store_online?&context=locator".format(location["id"]),
                meta={"item": item},
                callback=self.add_store_details,
            )

    def add_store_details(self, response):
        item = response.meta["item"]
        item["website"] = "https://www.crust.com.au" + response.xpath('//div[@class="store_container"]/a/@href').get()
        item["addr_full"] = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@class="store_container"]/p[1]/text()').getall()))
        )
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")
        item["email"] = response.xpath('//a[contains(@href, "mailto:")]/@href').get("").replace("mailto:", "")
        days_list = list(
            map(
                lambda x: x.split(",", 1)[0],
                filter(
                    None,
                    map(
                        str.strip, response.xpath('//div[@class="opening-hours"]/table/tbody/tr/td[1]/text()').getall()
                    ),
                ),
            )
        )
        hours_list = list(
            map(str.strip, response.xpath('//div[@class="opening-hours"]/table/tbody/tr/td[3]/text()').getall())
        )
        day_hours_array = list(zip(days_list, hours_list))
        hours_string = ""
        for day_hours in day_hours_array:
            hours_string = f"{hours_string} {day_hours[0]}: {day_hours[1]}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
