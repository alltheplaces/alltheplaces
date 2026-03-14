import json
import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature


class FarmersInsuranceUSSpider(SitemapSpider):
    name = "farmers_insurance_us"
    item_attributes = {"brand": "Farmers Insurance", "brand_wikidata": "Q1396863"}
    allowed_domains = ["agents.farmers.com"]
    sitemap_urls = ["https://agents.farmers.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/agents\.farmers\.com\/(\w{2})\/([-\w]+)\/([-\w]+)$",
            "parse_location",
        )
    ]

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)
        properties = {
            "ref": ref.strip("/"),
            "street_address": response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            "state": response.xpath('//abbr[@class="c-address-state"]/text()').extract_first(),
            "postcode": response.xpath('//span[@class="c-address-postal-code"]/text()').extract_first(),
            "phone": response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            "country": response.xpath(
                '//abbr[@class="c-address-country-name c-address-country-us"]/text()'
            ).extract_first(),
            "lat": float(response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
            "lon": float(response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
            "website": response.url,
        }

        hours_data = self.parse_hours(
            response.xpath(
                '//div[@class="c-location-hours-details-wrapper js-location-hours"]/@data-days'
            ).extract_first()
        )

        if hours_data:
            properties["opening_hours"] = hours_data
        yield Feature(**properties)

    def parse_hours(self, hours_data):
        if hours_data is None:
            return

        days = json.loads(hours_data)
        out_hours = []

        for day in days:
            start_day = day["day"][:2].title()
            intervals = day["intervals"]
            hours = ["%04d-%04d" % (interval["start"], interval["end"]) for interval in intervals]
            if len(intervals):
                out_hours.append("{} {}".format(start_day, ",".join(hours)))
        if len(out_hours):
            return "; ".join(out_hours)
