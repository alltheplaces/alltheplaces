from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class CalzedoniaSpider(SitemapSpider, StructuredDataSpider):
    name = "calzedonia"
    item_attributes = {"brand": "Calzedonia", "brand_wikidata": "Q1027874"}
    sitemap_urls = ["https://www.calzedonia.com/sitemap_index.xml"]
    sitemap_follow = ["stores"]
    sitemap_rules = [("/it/negozi/", "parse_sd")]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)
        item["city"] = clean_address(item.get("city"))
        item["opening_hours"] = OpeningHours()
        for row in response.xpath("//div[p]"):
            texts = [text.strip() for text in row.xpath("./p//text()").getall() if text.strip()]
            if len(texts) != 2 or not (day := sanitise_day(texts[0], DAYS_IT)):
                continue
            if "hiuso" in texts[1]:
                item["opening_hours"].set_closed(day)
                continue
            for time_range in texts[1].split(","):
                if "-" in time_range:
                    open_time, close_time = time_range.split("-")
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip())
        yield item
