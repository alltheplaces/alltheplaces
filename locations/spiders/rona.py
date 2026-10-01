import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class RonaSpider(SitemapSpider):
    name = "rona"
    item_attributes = {"brand": "Rona", "brand_wikidata": "Q3415283"}
    allowed_domains = ["www.rona.ca"]
    sitemap_urls = ["https://www.rona.ca/sitemap-stores-en.xml"]
    sitemap_rules = [("/store/", "parse_store")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = "CA"

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        day_hours = hours.xpath('.//li/time[@itemprop="openingHours"]/@datetime').getall()

        for open_hours in day_hours:
            day, open_close = open_hours.split(" ")
            open_time, close_time = open_close.split("-")
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M")

        return opening_hours

    def parse_store(self, response):
        phone_text = response.xpath('normalize-space(//div[@itemprop="telephone"]//text())').get()
        if phone_text:
            phone = "".join(re.findall(r"([0-9]+)", phone_text))
        else:
            phone = None

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('normalize-space(//*[@itemprop="name"]//text())').get(),
            "street_address": response.xpath('normalize-space(//span[@itemprop="streetAddress"]//text())').get(),
            "city": response.xpath('normalize-space(//span[@itemprop="addressLocality"]//text())').get(),
            "state": response.xpath('normalize-space(//span[@itemprop="addressRegion"]//text())').get(),
            "postcode": response.xpath('normalize-space(//span[@itemprop="postalCode"]//text())').get(),
            "country": "CA",
            "phone": phone,
            "website": response.url,
            "lat": float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').get()),
            "lon": float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').get()),
        }

        hours = response.xpath('(//ul[@class="storedetails__list storedetails__list-hours"])[1]')
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)

        yield Feature(**properties)
