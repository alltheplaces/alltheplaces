from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class SevenBrewUSSpider(SitemapSpider):
    name = "7_brew_us"
    allowed_domains = ["7brew.com"]
    start_urls = ["https://7brew.com"]
    item_attributes = {
        "brand": "7 Brew",
        "brand_wikidata": "Q127688691",
    }
    sitemap_urls = ["https://7brew.com/location-sitemap.xml"]
    sitemap_rules = [
        (r"/location/([-\w]+)/$", "parse"),
    ]

    def parse(self, response):
        item = Feature()

        item["ref"] = response.url.split("/")[-2]
        # Get coordinates from embedded Google Maps
        marker = response.css(".location-map .marker")
        item["lat"] = marker.attrib["data-lat"]
        item["lon"] = marker.attrib["data-lng"]

        contact = response.xpath("//h4[contains(text(), 'Contact')]/..")
        item["branch"] = contact.css("p:last-of-type strong::text").get()
        item["addr_full"] = contact.css("p:last-of-type::text").get()
        item["phone"] = contact.css("a[href^='tel:']::attr(href)").get()
        item["website"] = response.url

        hours_rows = response.css(".hours-area table tr")
        oh = OpeningHours()
        for row in hours_rows:
            day = row.css("td:first-child::text").get()
            hours = row.css("td:last-child::text").get()
            if not day or not hours:
                continue

            oh.add_ranges_from_string(f"{day}: {hours}")
        item["opening_hours"] = oh.as_opening_hours()

        return item
