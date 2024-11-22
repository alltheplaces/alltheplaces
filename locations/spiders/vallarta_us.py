from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class VallartaUSSpider(SitemapSpider):
    name = "vallarta_us"
    item_attributes = {"brand": "Vallarta Supermarkets", "brand_wikidata": "Q7911833"}
    allowed_domains = ["vallartasupermarkets.com"]
    sitemap_urls = ("https://vallartasupermarkets.com/store-sitemap.xml",)
    sitemap_rules = [(r"https://vallartasupermarkets.com/store-locations/[\w-]+/", "parse_store")]

    def parse_store(self, response):
        # No lat/lon in source code; Google map link contains address
        item = Feature()
        address = response.xpath("//div[@class='blade store-location']/div/div/div[2]/p[1]/text()").extract()

        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath("//div[@class='page-breadcrumb']/span/text()").extract_first()
        item["addr_full"] = address[1].strip()
        item["city"] = address[2].split(",")[0].strip()
        item["state"] = address[2].split(" ")[-2].strip()
        item["postcode"] = address[2].split(" ")[-1].strip()
        if phone := response.xpath("//a[@class='tel']/text()").extract_first():
            item["phone"] = phone.strip()
        try:
            if days := response.xpath("//div[contains(@class, 'days')]/text()").extract_first():
                if hours := response.xpath("//div[contains(@class, 'hours')]//p/text()").extract_first():
                    item["opening_hours"] = self.parse_hours(days.strip(), hours.strip())
        except Exception as e:
            self.logger.error(f"Failed to parse hours for {item['name']}, {e}")
        yield item

    def parse_hours(self, days, hours):
        opening_hours = OpeningHours()

        if "7 Days a Week" in days:
            open_time = hours.split(" - ")[0]
            close_time = hours.split(" - ")[1]

            for day in DAYS:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )
        else:
            return None

        return opening_hours.as_opening_hours()
