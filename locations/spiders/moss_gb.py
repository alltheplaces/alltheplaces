from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MossGBSpider(CrawlSpider, StructuredDataSpider):
    name = "moss_gb"
    item_attributes = {
        "brand": "Moss Bros",
        "brand_wikidata": "Q6916538",
        "country": "GB",
    }

    start_urls = ["https://www.moss.co.uk/store/finder"]
    rules = [Rule(LinkExtractor(allow=r"/store/([^/]+)$"), callback="parse_sd")]
    wanted_types = ["Store"]
    drop_attributes = {"facebook"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.xpath('//a[contains(@href,"maps.google.com")]'):
            coords = (
                response.xpath('//a[contains(@href,"maps.google.com/maps")]/@href')
                .get()
                .replace("https://maps.google.com/maps?hl=en&daddr=", "")
            )
            item["lat"], item["lon"] = coords.split(",")
        else:
            return
#       item["image"] = response.xpath('//*[@itemprop="image"]/@content').get()
        item["name"] = response.xpath('//li[@class="boldcopyright"][@itemprop="name"]/text()').get()
        item["branch"] = item.pop("name").removeprefix("Moss ")

        oh = OpeningHours()
        hours = response.xpath('//p[contains(@class,"store-opening-hours-text")]//text()').getall()
        for dayrange in hours:
            dayrange = dayrange.strip()
            if " to " in dayrange and "Holiday" not in dayrange:
                day, timerange = dayrange.split(" ", 1)
                open, close = timerange.split(" to ")
                if ":" not in open:
                    open = open.replace("am", ":00am")
                    open = open.replace("pm", ":00pm")
                if ":" not in close:
                    close = close.replace("pm", ":00pm")
                    close = close.replace("am", ":00am")
                oh.add_range(day, open, close, time_format="%I:%M%p")
        item["opening_hours"] = oh
        yield item
