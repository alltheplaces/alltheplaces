from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class DollarGeneralSpider(SitemapSpider):
    name = "dollar_general"
    item_attributes = {
        "brand": "Dollar General",
        "brand_wikidata": "Q145168",
        "country": "US",
        "extras": Categories.SHOP_VARIETY_STORE.value,
    }
    allowed_domains = ["dollargeneral.com"]
    sitemap_urls = ["https://www.dollargeneral.com/sitemap-main.xml"]
    sitemap_rules = [(r"https:\/\/www\.dollargeneral\.com\/store-directory\/\w{2}\/.*\/\d+$", "parse")]

    def parse(self, response):
        properties = {
            "street_address": response.xpath("//@data-address").extract_first(),
            "city": response.xpath("//div[@data-city]/@data-city").extract_first(),
            "state": response.xpath("//div[@data-state]/@data-state").extract_first(),
            "postcode": response.xpath("//div[@data-zip]/@data-zip").extract_first(),
            "lat": response.xpath("//div[@data-latitude]/@data-latitude").extract_first(),
            "lon": response.xpath("//div[@data-longitude]/@data-longitude").extract_first(),
            "phone": response.xpath("//div[@data-phone]/@data-phone").extract_first(),
            "website": response.url,
            "ref": response.url.rsplit("/", 1)[-1].rsplit(".")[0],
        }

        o = OpeningHours()
        for d in DAYS_FULL:
            hours = response.xpath(f"//@data-{d.lower()}").get()
            if not hours:
                continue
            from_time, to_time = hours.split(":")
            o.add_range(d, from_time, to_time, "%H%M")

        properties["opening_hours"] = o.as_opening_hours()

        yield Feature(**properties)
