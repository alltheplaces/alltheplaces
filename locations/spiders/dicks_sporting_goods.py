import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class DicksSportingGoodsSpider(SitemapSpider):
    name = "dicks_sporting_goods"
    item_attributes = {"brand": "Dick's Sporting Goods", "brand_wikidata": "Q5272601"}
    allowed_domains = ["dickssportinggoods.com"]
    sitemap_urls = ["https://stores.dickssportinggoods.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/(\d+)/", "parse_store")]

    def parse_hours(self, response):
        days = response.xpath('//meta[@property="business:hours:day"]/@content').extract()
        start_times = response.xpath('//meta[@property="business:hours:start"]/@content').extract()
        end_times = response.xpath('//meta[@property="business:hours:end"]/@content').extract()
        opening_hours = OpeningHours()
        for day, open_time, close_time in zip(days, start_times, end_times):
            opening_hours.add_range(day, self.fix_hours(open_time), self.fix_hours(close_time))
        return opening_hours

    def fix_hours(self, hours_str):
        if ":" not in hours_str:
            hours_str = hours_str + ":00"
        return hours_str

    def parse_store(self, response):
        ref = re.search(r"/(\d+)/$", response.url).group(1)
        name = response.xpath('//meta[@property="og:title"]/@content').get()
        if "GOING, GOING, GONE!" in name:
            name = "Going, Going, Gone!"
            branch = response.xpath('//div[@class="addressBlock"]//h1/text()[2]').get()
        else:
            name = "Dick's Sporting Goods"
            branch = response.xpath('//div[@class="addressBlock"]//h1/text()').get()

        yield Feature(
            lat=float(response.xpath('//meta[@property="place:location:latitude"]/@content').extract_first()),
            lon=float(response.xpath('//meta[@property="place:location:longitude"]/@content').extract_first()),
            street_address=response.xpath(
                '//meta[@property="business:contact_data:street_address"]/@content'
            ).extract_first(),
            city=response.xpath('//meta[@property="business:contact_data:locality"]/@content').extract_first(),
            state=response.xpath('//meta[@property="business:contact_data:region"]/@content').extract_first(),
            postcode=response.xpath('//meta[@property="business:contact_data:postal_code"]/@content').extract_first(),
            country=response.xpath('//meta[@property="business:contact_data:country_name"]/@content').extract_first(),
            phone=response.xpath('//meta[@property="business:contact_data:phone_number"]/@content').extract_first(),
            website=response.xpath('//meta[@property="business:contact_data:website"]/@content').extract_first(),
            ref=ref,
            name=name,
            branch=branch,
            opening_hours=self.parse_hours(response),
        )
