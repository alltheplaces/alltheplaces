from scrapy import FormRequest, Selector, Spider

from locations.hours import DAYS_RS, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class DexyRSSpider(Spider):
    name = "dexy_rs"
    item_attributes = {"brand": "Dexy Co", "brand_wikidata": "Q97192674"}
    start_urls = ["https://www.dexy.co.rs/radnje"]

    def parse(self, response, **kwargs):
        for city in response.xpath('//div[contains(@id, "collapseOne")]/@id').getall():
            yield FormRequest(
                url="https://www.dexy.co.rs/radnje",
                formdata={
                    "ajax": "yes",
                    "task": "loadstoresforcity",
                    "city": city.replace("collapseOne", ""),
                },
                callback=self.parse_city,
            )

    def parse_city(self, response, **kwargs):
        sel = Selector(text=response.json()["html"])
        for location in sel.xpath("//div[@data-storeid]"):
            item = Feature()
            item["ref"] = location.xpath("@data-storeid").get()
            item["street_address"] = location.xpath(".//@title").get()
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-lng").get()
            # The website currently 404s
            # item["website"] = location.xpath('.//a[contains(@href, "https://www.dexy.co.rs/")]/@href').get()
            extract_phone(item, location)

            item["opening_hours"] = OpeningHours()
            for rule in location.xpath('.//div[@class="day"]'):
                if day := sanitise_day(rule.xpath("./dt/text()").get(), DAYS_RS):
                    times = rule.xpath("./dd/text()").get().strip()
                    if " - " in times:
                        start_time, end_time = times.split(" - ")
                        item["opening_hours"].add_range(day, start_time, end_time, time_format="%H:%M:%S")

            yield item
