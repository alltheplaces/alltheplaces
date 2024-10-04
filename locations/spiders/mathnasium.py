import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

center_page_regex = re.compile(r"(/(?P<country>\w\w)(-\w\w)?)?/maths?-cent[er]{2}s/([\w-]+)$")


class MathnasiumSpider(SitemapSpider, StructuredDataSpider):
    name = "mathnasium"
    item_attributes = {"brand": "Mathnasium", "brand_wikidata": "Q6787302"}
    sitemap_urls = ["https://www.mathnasium.com/sitemap/sitemap-index.xml"]
    sitemap_rules = [(center_page_regex, "parse_sd")]
    sitemap_follow = [r"/sitemap/[\w-]+/sitemap-center-pages.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        del item["name"]
        item["branch"] = response.xpath("//input[@id='center_name']/@value").get()
        item["extras"]["contact:sms"] = (
            response.xpath("//a[starts-with(@href, 'sms:')]/@href").get("").removeprefix("sms:")
        )
        item["country"] = (center_page_regex.search(response.url).group("country") or "US").upper()
        item["ref"] = item["country"] + response.xpath("//input[@id='center_id']/@value").get()

        if item.get("twitter", "").lower() == "mathnasium":
            del item["twitter"]

        if item.get("facebook") == "https://www.facebook.com/mathnasium":
            del item["facebook"]

        oh_instructional = OpeningHours()
        for row in response.xpath('//div[@class="hours"]/div[@class="schedule"][1]//tr'):
            oh_instructional.add_ranges_from_string(row.xpath("string(.)").get())
        item["opening_hours"] = oh_instructional

        oh_office = OpeningHours()
        for row in response.xpath('//div[@class="hours"]/div[@class="schedule"][2]//tr'):
            oh_office.add_ranges_from_string(row.xpath("string(.)").get())
        item["extras"]["opening_hours:office"] = oh_office.as_opening_hours()

        yield item
