from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_SR, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BipaHRSpider(Spider):
    name = "bipa_hr"
    item_attributes = {
        "brand": "Bipa",
        "brand_wikidata": "Q864933",
    }
    start_urls = ["https://bipa.hr/poslovnice/"]

    def parse(self, response: Response):
        for store in response.xpath('//*[@class="entry-list__entries-col col-12 col-md-4 marker"]'):
            item = Feature()
            item["name"] = store.xpath(".//@data-name").get()
            item["lat"] = store.xpath(".//@data-lat").get()
            item["lon"] = store.xpath(".//@data-lng").get()
            item["street_address"] = store.xpath(".//address//text()[1]").get()
            item["addr_full"] = merge_address_lines(
                [item["street_address"], store.xpath(".//address//text()[1]").get()]
            )
            item["ref"] = store.xpath(".//article/@class").get()
            oh = OpeningHours()

            for day_time in store.xpath(".//ul//li"):
                day_time_string = day_time.xpath("normalize-space()").get()
                oh.add_ranges_from_string(day_time_string.strip(), days=DAYS_SR)
            item["opening_hours"] = oh
            yield item
