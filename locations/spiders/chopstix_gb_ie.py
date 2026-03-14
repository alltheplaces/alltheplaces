import chompjs
from scrapy import Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class ChopstixGBIESpider(JSONBlobSpider):
    name = "chopstix_gb_ie"
    item_attributes = {"brand": "Chopstix", "brand_wikidata": "Q115327253"}
    start_urls = ["https://www.powr.io/map/u/f2d4aea4_1617743451"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    handle_httpstatus_list = [404]

    def extract_json(self, response):
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "window.CONTENT")]/text()').get())
        return data["locations"]

    def post_process_item(self, item, response, feature):
        item["ref"] = feature.get("idx")
        item["branch"] = item.pop("name", None)
        if item.get("branch"):
            item["branch"] = (
                item["branch"]
                .removeprefix("Chopstix Noodle Bar - ")
                .removeprefix("Chopstix Express ")
                .removeprefix("Chopstix - ")
                .removeprefix("Chopstix – ")
            )

        apply_category(Categories.FAST_FOOD, item)
        if item.get("website"):
            # Avoid 301 redirect from bare domain to www
            item["website"] = item["website"].replace("://chopstixnoodles.co.uk", "://www.chopstixnoodles.co.uk")
            yield Request(
                url=item["website"],
                callback=self.parse_store_page,
                cb_kwargs={"item": item},
            )
        else:
            yield item

    def parse_store_page(self, response, item):
        if response.status == 404:
            yield item
            return

        oh = OpeningHours()
        oh.add_ranges_from_string(
            response.xpath('//h4[contains(text(), "OPENING HOURS")]/following-sibling::p').get("")
        )
        item["opening_hours"] = oh

        item["phone"] = response.xpath('//h4[contains(text(), "STORE NUMBER")]/following-sibling::p/text()').get()
        item["addr_full"] = response.xpath('//h4[contains(text(), "ADDRESS")]/following-sibling::p[1]').get()

        yield item
