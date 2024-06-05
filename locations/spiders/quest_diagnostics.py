from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class QuestDiagnosticsSpider(SitemapSpider):
    name = "quest_diagnostics"
    item_attributes = {"brand": "Quest Diagnostics", "brand_wikidata": "Q7271456"}
    allowed_domains = ["www.questdiagnostics.com"]
    sitemap_urls = ["https://www.questdiagnostics.com/locations-sitemap.xml"]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "lat": response.xpath('//div[@class="latitude"]/text()').get(),
            "lon": response.xpath('//div[@class="longitude"]/text()').get(),
            "name": response.xpath('//div[@class="location-detail-title"]/text()').extract_first().strip(),
            "website": response.url,
            "phone": response.xpath('//a[@id="phone"]/text()').extract_first(),
            "addr_full": clean_address(response.xpath('//div[@class="address"]/text()').getall()),
        }

        if not properties["name"]:
            # Invalid location
            return

        fax = response.xpath('//a[@id="fax"]/text()').extract_first()
        if fax:
            properties["extras"] = {"fax": fax}

        oh = OpeningHours()
        for day in DAYS_FULL:
            hour = response.xpath(
                '//div[@class="week-time-content"]/ul/li/p[contains(text(), $day)]/following-sibling::span/text()',
                day=day,
            ).get("")
            for x in hour.split(" , "):
                try:
                    open_time, close_time = x.split("-")
                    oh.add_range(day, open_time, close_time, "%I:%M %p")
                except ValueError:
                    pass

        properties["opening_hours"] = oh.as_opening_hours()

        yield Feature(**properties)
