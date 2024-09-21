import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class RonaSpider(SitemapSpider):
    name = "rona"
    item_attributes = {"brand": "RONA", "brand_wikidata": "Q3415283"}
    allowed_domains = ["www.rona.ca"]
    sitemap_urls = ["https://www.rona.ca/sitemap-stores-en.xml"]
    sitemap_rules = [("/store/", "parse_store")]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        day_hours = hours.xpath('.//li/time[@itemprop="openingHours"]/@datetime').extract()

        for open_hours in day_hours:
            day, open_close = open_hours.split(" ")
            open_time, close_time = open_close.split("-")
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        phone_text = response.xpath('normalize-space(//div[@itemprop="telephone"]//text())').extract_first()
        if phone_text:
            phone = "".join(re.findall(r"([0-9]+)", phone_text))
        else:
            phone = None

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').extract_first(),
            "street_address": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]//text())'
            ).extract_first(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').extract_first(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').extract_first(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').extract_first(),
            "country": "CA",
            "phone": phone,
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        hours = response.xpath('(//ul[@class="storedetails__list storedetails__list-hours"])[1]')
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)

        yield Feature(**properties)
