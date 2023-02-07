from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class NaturalGrocersSpider(SitemapSpider):
    name = "natural_grocers"
    item_attributes = {"brand": "Natural Grocers", "brand_wikidata": "Q17146520"}
    allowed_domains = ["naturalgrocers.com"]
    sitemap_urls = ["https://www.naturalgrocers.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"/store/",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        item = Feature(
            ref=response.url,
            website=response.url,
            name=response.css(".node-title span::text").get().strip(),
            lat=response.xpath('//div[@id="main"]//meta[@property="latitude"]').attrib["content"],
            lon=response.xpath('//div[@id="main"]//meta[@property="longitude"]').attrib["content"],
            addr_full=response.xpath('//div[@id="main"]').css(".address-line1::text").get(),
            city=response.xpath('//div[@id="main"]').css(".locality::text").get(),
            state=response.xpath('//div[@id="main"]').css(".administrative-area::text").get(),
            postcode=response.xpath('//div[@id="main"]').css(".postal-code::text").get(),
            country=response.xpath('//div[@id="main"]').css(".country::text").get(),
            opening_hours=self.get_hours(response),
        )

        yield item

    def get_hours(self, response):
        o = OpeningHours()
        for days, hours in zip(
            response.css(".store-info.store-hours .office-hours__item-label::text").getall(),
            response.css(".store-info.store-hours .office-hours__item-slots::text").getall(),
        ):
            days = [sanitise_day(d.strip(" :")) for d in days.split("-")]
            if len(days) == 2:
                days = day_range(*days)
            for day in days:
                o.add_range(day, *hours.split("-"), "%I:%M %p")

        return o.as_opening_hours()
