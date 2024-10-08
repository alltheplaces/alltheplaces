from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class PradaSpider(SitemapSpider, StructuredDataSpider):
    name = "prada"
    item_attributes = {"brand": "Prada", "brand_wikidata": "Q193136"}
    allowed_domains = ["www.prada.com"]
    sitemap_urls = ["https://www.prada.com/us/en/sitemap.xml"]
    sitemap_rules = [("/store-locator/store", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        item["ref"] = response.xpath('//div[contains(@class, "singleStore")]/@data-store-id').extract_first()

        # Note that some stores open and close multiple times per day, hence the somewhat complicated OpeningHours extraction that follows.
        hours_raw = (
            ld_data["openingHours"]
            .replace("--", "0:00 am - 0:00 am")
            .replace("-", "")
            .replace(" am", "AM")
            .replace(" pm", "PM")
            .split()
        )
        oh = OpeningHours()
        current_day = None
        start_time = None
        for segment in hours_raw:
            if segment in DAYS_EN:
                current_day = DAYS_EN[segment]
            elif start_time is None:
                start_time = segment
            else:
                if start_time != "0:00AM" and segment != "0:00AM":
                    oh.add_range(current_day, start_time, segment, "%I:%M%p")
                start_time = None
        item["opening_hours"] = oh.as_opening_hours()

        yield item
