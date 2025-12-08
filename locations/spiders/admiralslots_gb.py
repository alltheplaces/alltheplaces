from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class AdmiralslotsGBSpider(SitemapSpider):
    name = "admiralslots_gb"
    item_attributes = {"brand": "Admiral", "brand_wikidata": "Q25205850"}
    sitemap_urls = ["https://www.admiralslots.co.uk/venue-sitemap.xml"]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url

        item["branch"] = response.xpath('//div[@class="m__hero__content"]/h1/text()').get()
        item["addr_full"] = response.xpath('//div[@class="m__hero__content"]/h6/text()').get()

        item["image"] = response.xpath(
            '//*[@data-bkimage][@class="bk "][not(contains(@data-bkimage, "eneric"))]/@data-bkimage'
        ).get()

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//ul[@class="nolist opening-times"]/li'):
            day, times = rule.xpath("./span/text()").getall()
            if "CLOSED" in times.upper():
                item["opening_hours"].set_closed(day)
            try:
                start_time, end_time = times.split("-")
                item["opening_hours"].add_range(day, start_time.strip(), end_time.strip())
            except:
                pass

        extract_phone(item, response)
        extract_google_position(item, response)

        yield item
