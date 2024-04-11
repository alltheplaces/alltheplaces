from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class vhlDESpider(SitemapSpider, StructuredDataSpider):
    name = "vhl_de"
    item_attributes = {"brand": "Vereinigte Lohnsteuerhilfe e.V.", "brand_wikidata": "Q15852617"}
    sitemap_urls = [
        "https://www.vlh.de/sitemap.bst.xml",
    ]
    sitemap_rules = [(r"/\d+/Oeffnungszeiten.html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)
        item["phone"] = ld_data["telephone"]
        item["website"] = item["website"].replace("Oeffnungszeiten.html", "")
        item["name"] = response.xpath("/html/head/title/text()").get().replace("Öffnungszeiten | ", "")

        opening_hours = self.parse_opening_hours(response)

        if opening_hours:
            item["opening_hours"] = opening_hours
        yield item

    def parse_opening_hours(self, response):
        opening_hours = OpeningHours()

        table = response.xpath('//table[@id="office-hours-table"]')
        for row in table.xpath("./tr"):
            day = row.xpath("./td/text()").extract()[0]
            times = row.xpath("./td/text()").extract()[1:]

            for time in times:
                open_time, close_time = time.split(" - ")
                opening_hours.add_range(DAYS_DE.get(day.title()), open_time.strip(), close_time.strip())

        return opening_hours
