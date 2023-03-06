from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class SchnitzAUSpider(SitemapSpider):
    name = "schnitz_au"
    item_attributes = {"brand": "Schnitz", "brand_wikidata": "Q48792277"}
    sitemap_urls = ["https://schnitz.com.au/store-sitemap.xml"]
    sitemap_rules = [(r"\/stores\/(.+)", "parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//div[contains(@class, "hero-module__text-lockup")]/div/h1/text()').get().strip(),
            "lat": response.xpath('//div/@data-lat').get().strip(),
            "lon": response.xpath('//div/@data-lng').get().strip(),
            "addr_full": response.xpath('//div[contains(@class, "hero-module__contact")]/div/div[1]/text()').get().strip(),
            "phone": response.xpath('//div[contains(@class, "hero-module__contact")]/div/div[2]/text()').get(),
            "website": response.url,
        }
        if properties["phone"]:
            properties["phone"] = properties["phone"].strip()
        
        oh = OpeningHours()
        hours_raw = (" ".join(response.xpath('//ul[contains(@class, "single-store-content__details-oh-list")]/li/span/text()').getall())).replace("26th January", "Jan26").replace("Closed", "0:00 am to 0:00 am").replace(" to ", " ").replace(" am", "AM").replace(" pm", "PM").split()
        hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
        for day in hours_raw:
            if day[0] == "Jan26":
                continue
            if day[1] == "0:00AM" and day[2] == "0:00AM":
                continue
            oh.add_range(DAYS_EN[day[0]], day[1], day[2], "%I:%M%p")
        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
