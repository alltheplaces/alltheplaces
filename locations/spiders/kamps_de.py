from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS, DAYS_DE, OpeningHours
from locations.items import Feature


class KampsDESpider(SitemapSpider):
    name = "kamps_de"
    item_attributes = {"brand": "Kamps", "brand_wikidata": "Q1723381"}
    sitemap_urls = ("https://kamps.de/sitemap.xml",)
    sitemap_rules = [
        (r"/standort/", "parse"),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        properties = {
            "ref": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "phone": response.xpath('//a[contains(@href, "tel:")]/text()').extract_first(),
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "street_address": response.xpath('//div[@class="card-block"]/p/text()').extract()[0].strip(),
            "city": response.xpath('//div[@class="card-block"]/p/text()').extract()[1].strip().split(" ", 1)[1],
            "postcode": response.xpath('//div[@class="card-block"]/p/text()').extract()[1].strip().split(" ", 1)[0],
        }

        oh = OpeningHours()
        for row in response.xpath('//div[@class="card-block"]/table/tr'):
            day_de = row.xpath("./td/text()")[0].extract()
            range_str = row.xpath("./td/text()")[-1].extract()
            if range_str == "24 Stunden":
                oh.add_days_range(DAYS, "00:00", "23:59")
            if "geschlossen" in range_str:
                return
            times = range_str.replace("–", "-")
            if "-" in times:
                for time in times.split(","):
                    range_start, range_end = map(str.strip, time.split("-"))
                    oh.add_range(DAYS_DE[day_de], range_start, range_end)

        properties["opening_hours"] = oh.as_opening_hours()

        extract_google_position(properties, response)

        yield Feature(**properties)
