from chompjs import parse_js_object
from scrapy import Selector

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulGBSpider(JSONBlobSpider):
    name = "paul_gb"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paul-uk.com/find-a-paul"]
    websites = {}

    def extract_json(self, response):
        for location in response.xpath('.//div[@class="store"]'):
            ref = location.xpath("@id").get()
            website = location.xpath('.//a[contains(@href, "https://www.paul-uk.com/find-a-paul/")]/@href').get()
            self.websites[ref] = website
        data_raw = response.xpath(
            '//script[contains(text(), "BestResponseMedia_FindPaul/js/storelocator")]/text()'
        ).get()
        return parse_js_object(data_raw.split('storeList":', 1)[1])

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("PAUL", "").replace("PAUL Express", "").strip()
        item["website"] = self.websites[item["ref"]]
        info = Selector(text=location["info"])
        item["addr_full"] = clean_address([info.xpath(".//p[1]/text()").get()] + info.xpath(".//div/text()").getall())
        item["phone"] = info.xpath(".//p[2]/text()").get()
        item["opening_hours"] = OpeningHours()
        for day in info.xpath(".//div[2]/p/text()").getall():
            item["opening_hours"].add_ranges_from_string(day)
        yield item
