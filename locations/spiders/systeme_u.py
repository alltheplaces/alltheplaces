import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SystemeUSpider(scrapy.Spider):
    name = "systeme_u"
    item_attributes = {"brand": "Systeme U", "brand_wikidata": "Q2529029"}
    allowed_domains = ["magasins-u.com"]
    start_urls = [
        "https://www.magasins-u.com/sitemap.xml",
    ]
    requires_proxy = "FR"  # Proxy or other captcha drama?
    brands = {
        "uexpress": {"brand": "U Express", "brand_wikidata": "Q2529029"},
        "superu": {"brand": "Super U", "brand_wikidata": "Q2529029"},
        "marcheu": {"brand": "Marché U", "brand_wikidata": "Q2529029"},
        "hyperu": {"brand": "Hyper U", "brand_wikidata": "Q2529029"},
    }

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        days = hours[0].split(",")

        for d in days:
            times = d.split(" ")
            day = times[0]
            if times[1] == "Fermé":
                pass
            else:
                open_time, close_time = times[1].split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//*[@id="libelle-magasin"]/text()').extract_first(),
            "addr_full": response.xpath('normalize-space(//*[@itemprop="streetAddress"]/text())').extract_first(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/text()').extract_first(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').extract_first(),
            "country": "FR",
            "lat": response.xpath("//@data-store-latitude").extract_first(),
            "lon": response.xpath("//@data-store-longitude").extract_first(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').extract_first(),
            "website": response.url,
        }

        if m := re.search(r"/(magasin|station)/(uexpress|superu|marcheu|hyperu)-\w+", response.url):
            if m.group(1) == "magasin":
                apply_category(Categories.SHOP_SUPERMARKET, properties)
            else:
                apply_category(Categories.FUEL_STATION, properties)

            properties.update(self.brands[m.group(2)])

        try:
            h = self.parse_hours(response.xpath('//*[@itemprop="openingHours"]/@content').extract())

            if h:
                properties["opening_hours"] = h
        except:
            pass

        yield Feature(**properties)

    def parse(self, response):
        xml = scrapy.selector.Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            try:
                type = re.search(r"com\/(.*?)\/", url).group(1)
                if type in ["magasin", "station"]:
                    yield scrapy.Request(url, callback=self.parse_stores)
            except:
                pass
