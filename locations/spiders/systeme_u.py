import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
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

        for hour in hours:

            # Check if the hour data indicates 24/7 availability
            hour_text = hour.get()
            if hour_text:
                hour_text = hour_text.strip()

            if "24h/24 - 7j/7" in hour_text:
                for day in DAYS_FR.values():
                    opening_hours.add_range(
                        day=day,
                        open_time="00:00",
                        close_time="24:00",
                        time_format="%H:%M",
                    )
                continue

            day = hour.xpath('.//td[@class="day"]/text()').extract_first()
            schedule = hour.xpath('.//td[@class="schedule"]/text()').extract_first()

            if schedule and schedule.lower() != "fermé":
                open_time, close_time = schedule.split(" - ")
                opening_hours.add_range(
                    day=DAYS_FR[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//div[@class="info-magasin-station"]/h1[@class="h1"]/text()').extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//div[@class="address b-md b-md--sm"]/p[1]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//div[@class="address b-md b-md--sm"]/p[2]/span[2]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//div[@class="address b-md b-md--sm"]/p[2]/span[1]/text())'
            ).extract_first(),
            "country": "FR",
            "lat": response.xpath("//@data-store-latitude").extract_first(),
            "lon": response.xpath("//@data-store-longitude").extract_first(),
            "phone": response.xpath('//div[@class="phone-number b-md"]/text()').extract_first(),
            "website": response.url,
        }

        if m := re.search(r"/(magasin|station)/(uexpress|superu|marcheu|hyperu)-\w+", response.url):
            if m.group(1) == "magasin":
                apply_category(Categories.SHOP_SUPERMARKET, properties)
                hours_xpath = '//div[@id="magasin-tab"]//div[@class="u-horaire"]//tr[@class="u-horaire__line-day"]'
            else:
                apply_category(Categories.FUEL_STATION, properties)
                hours_xpath = '//div[@class="u-station__magasin"]/p[2]/text()'

            properties.update(self.brands[m.group(2)])

        try:
            hours = response.xpath(hours_xpath)
            h = self.parse_hours(hours)

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
