from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours, day_range
from locations.items import Feature


class SeattleCoffeeCompanySpider(SitemapSpider):
    name = "seattle_coffee_company"
    item_attributes = {"brand": "Seattle Coffee Company", "brand_wikidata": "Q116646221"}
    sitemap_urls = [
        "https://www.seattlecoffeecompany.co.za/sitemap_index.xml",
    ]
    sitemap_follow = ["store"]
    skip_auto_cc_domain = True

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//title/text()").get().replace(self.item_attributes["brand"], "").strip("- ")
        item["addr_full"] = response.xpath('//*[contains(@class,"jet-listing-dynamic-field__content")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//div[contains(@class, "trading")]').xpath("normalize-space()").getall():
            if ("Closed" in day_time) or ("Church Services" in day_time):
                continue
            if "24/7" in day_time:
                item["opening_hours"] = "24/7"
            else:
                try:
                    day, time = day_time.replace(" - ", "-").split(" ")
                    if "-" in day:
                        start_day, end_day = day.split("-")
                        open_time, close_time = time.split("-")
                        if ":" not in open_time:
                            open_time = open_time.replace("am", ":00AM")
                        if ":" not in close_time:
                            close_time = close_time.replace("pm", ":00PM")
                        if end_day == "Holidays":
                            end_day = start_day
                        item["opening_hours"].add_days_range(
                            day_range(start_day, end_day), open_time, close_time, time_format="%I:%M%p"
                        )
                except:
                    item["opening_hours"] = ""

        yield item
