import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class WaterstonesSpider(scrapy.Spider):
    name = "waterstones"
    item_attributes = {"brand": "Waterstones", "brand_wikidata": "Q151779"}
    allowed_domains = ["www.waterstones.com"]
    start_urls = ["https://www.waterstones.com/bookshops/directory/"+chr(i) for i in range(ord('a'), ord('z')+1)]
    # Use the alphabetical list pages rather than the paginated "view
    # all" list used previously, since in the latter the final page
    # is not reached by a rel=next link.
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response):
        stores = response.xpath('//div[contains(@class, "shops-directory-list")]//a/@href').extract()
        stores = set(stores)
        for store in stores:
            yield response.follow(store, self.parse_store)

    def parse_store(self, response):
        try:
            ref = response.url.split("/")[4]
        except IndexError:
            # No bookshop
            return

        properties = {
            "ref": ref,
            "name": self.get_meta_property(response, "og:title"),
            "addr_full": self.get_meta_property(response, "business:contact_data:street_address"),
            "city": self.get_meta_property(response, "business:contact_data:locality"),
            "postcode": self.get_meta_property(response, "business:contact_data:postal_code"),
            "lat": self.get_meta_property(response, "place:location:latitude"),
            "lon": self.get_meta_property(response, "place:location:longitude"),
            "phone": self.get_meta_property(response, "business:contact_data:phone_number"),
            "opening_hours": self.get_opening_hours(response),
            "website": response.url,
        }
        yield Feature(**properties)

    def get_meta_property(self, response, property):
        return response.xpath(f'//meta[@property="{property}"]/@content').extract_first()

    def get_opening_hours(self, response):
        try:
            days = response.xpath('//meta[@property="business:hours:day"]/@content').extract()
            starts = response.xpath('//meta[@property="business:hours:start"]/@content').extract()
            ends = response.xpath('//meta[@property="business:hours:end"]/@content').extract()
            o = OpeningHours()
            for i in range(len(days)):
                day = days[i][0].upper() + days[i][1]
                start = starts[i].replace(".", ":")
                end = ends[i].replace(".", ":")
                if day and start and end:
                    o.add_range(day, start, end)
            return o.as_opening_hours()
        except IndexError:
            # No opening hours provided
            pass
