from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.hours import DAYS_PL, DELIMITERS_PL, OpeningHours
from locations.items import Feature


class OdidoPLSpider(SitemapSpider):
    name = "odido_pl"
    item_attributes = {"brand": "Odido", "brand_wikidata": "Q106947294"}
    sitemap_urls = ["https://www.sklepy-odido.pl/sitemap.xml"]
    sitemap_rules = [("-sklep/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath('//*[@class="store-address"]/text()').get()
        extract_google_position(item, response)
        date_time = response.css(".date-time")
        if date_time:
            item["opening_hours"] = OpeningHours()
            days = date_time.css(".days::text").getall()
            hours = date_time.css(".time::text").getall()
            for day, hour in zip(days, hours):
                if hour == "Zamknięte":
                    continue
                item["opening_hours"].add_ranges_from_string(f"{day} {hour}", days=DAYS_PL, delimiters=DELIMITERS_PL)
        yield item
