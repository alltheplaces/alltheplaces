import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PostieNZSpider(CrawlSpider, StructuredDataSpider):
    name = "postie_nz"
    item_attributes = {
        "brand": "Postie",
        "brand_wikidata": "Q110299434",
    }
    start_urls = ["https://www.postie.co.nz/stores/all"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.postie\.co\.nz\/store-detail\/southern\/[\w-]+"),
            callback="parse",
        ),
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.postie\.co\.nz\/store-detail\/northern\/[\w-]+"),
            callback="parse",
        ),
    ]
    time_format = "%I:%M%p"

    def pre_process_data(self, ld_data, **kwargs):
        new_hours = []
        for day in ld_data["openingHours"]:
            new_day = re.sub(r"(\s\d{1,2})am", r"\1:00am", day)
            new_day = re.sub(r"([-\s–]\d{1,2})pm", r"\1:00pm", new_day)
            new_day = re.sub(r"(\d)\.(\d)", r"\1:\2", new_day)
            new_hours.append(new_day.strip())
        ld_data["openingHours"] = new_hours
