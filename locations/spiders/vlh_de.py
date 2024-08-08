from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class VlhDESpider(SitemapSpider, StructuredDataSpider):
    name = "vlh_de"
    item_attributes = {"brand": "Vereinigte Lohnsteuerhilfe", "brand_wikidata": "Q15852617"}
    sitemap_urls = [
        "https://www.vlh.de/sitemap.bst.xml",
    ]
    sitemap_rules = [(r"\/bst\/\d+\/*$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data):
        item.pop("image", None)
        item["phone"] = ld_data["telephone"]
        item["name"] = None  # It's cleaner to just use name from NSI
        self.parse_opening_hours(item, response)
        yield item

    def parse_opening_hours(self, item: Feature, response: Response):
        try:
            table = response.xpath('//table[@class="table time-table"]')
            if table:
                # It can be two tables, first is actual hours, second is phone availability hours
                table = table[0]
            else:
                return

            oh = OpeningHours()

            for row in table.xpath("./tr"):
                day = row.xpath("./td/text()").extract()[0]
                times = row.xpath("./td/text()").extract()[1:]

                for time in times:
                    time.strip()
                    time = time.replace("Uhr", "")
                    if not time:
                        continue

                    open_time, close_time = time.split(" - ")
                    day = day.replace(":", "")
                    oh.add_range(DAYS_DE.get(day.title()), open_time.strip(), close_time.strip())

            item["opening_hours"] = oh.as_opening_hours()

        except Exception as e:
            self.logger.warning(f'Failed to parse opening hours for {item["ref"]}, {e}')
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
