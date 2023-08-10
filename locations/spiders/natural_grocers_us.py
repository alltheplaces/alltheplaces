from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Spider

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


# Paging links are added by js, so this can't currently be a CrawlSpider
class NaturalGrocersUSSpider(Spider):
    name = "natural_grocers_us"
    item_attributes = {"brand": "Natural Grocers", "brand_wikidata": "Q17146520"}
    allowed_domains = ["naturalgrocers.com"]
    link_extractor = LinkExtractor(allow="/store/")

    def start_requests(self):
        yield Request("https://www.naturalgrocers.com/store-directory?page=0", meta={"page": 0})

    def parse(self, response: Response, **kwargs):
        links = self.link_extractor.extract_links(response)
        if len(links) == 1:
            return
        else:
            next_page = response.meta["page"] + 1
            yield Request(f"https://www.naturalgrocers.com/store-directory?page={next_page}", meta={"page": next_page})

            for link in links:
                yield Request(link.url, callback=self.parse_store)

    def parse_store(self, response):
        item = Feature(
            ref=response.url,
            website=response.url,
            name=response.css(".node-title span::text").get().strip(),
            lat=response.xpath('//div[@id="main"]//meta[@property="latitude"]').attrib["content"],
            lon=response.xpath('//div[@id="main"]//meta[@property="longitude"]').attrib["content"],
            street_address=response.xpath('//div[@id="main"]').css(".address-line1::text").get(),
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
