import chompjs
import scrapy

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class TheGoodGuysAUSpider(StructuredDataSpider):
    name = "the_good_guys_au"
    item_attributes = {"brand": "The Good Guys", "brand_wikidata": "Q7737217"}
    allowed_domains = ["www.thegoodguys.com.au"]
    start_urls = ["https://www.thegoodguys.com.au/stores"]

    def parse(self, response):
        data_json = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"allStoresData")]/text()').extract_first()
        )
        for store in data_json["state"]["loaderData"]["routes/stores._index"]["allStoresData"]["stores"]:
            yield scrapy.Request(
                url="https://www.thegoodguys.com.au/stores/" + store["storeUrl"], callback=self.parse_sd
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day_time in ld_data["openingHoursSpecification"]:
            day = day_time["dayOfWeek"].replace("http://schema.org/", "")
            open_time = day_time["opens"]
            close_time = day_time["closes"]
            item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
