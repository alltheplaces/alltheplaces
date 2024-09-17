from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.open_graph_spider import OpenGraphSpider


class BudgensGBSpider(SitemapSpider, OpenGraphSpider):
    name = "budgens_gb"
    item_attributes = {"brand": "Budgens", "brand_wikidata": "Q4985016"}
    sitemap_urls = ["https://www.budgens.co.uk/sitemap.xml"]
    sitemap_rules = [("/our-stores/", "parse")]

    def post_process_item(self, item, response, **kwargs):
        item["street_address"] = item["street_address"].strip(",")

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//tr[@class="openingHours"]'):
            day = rule.xpath('./td[@class="day"]/text()').get().strip(" :")
            times = rule.xpath('./td[@class="hour"]/text()').get().split("-")
            if times == ["24hr "]:
                times = ["00:00", "24:00"]
            elif times == ["Closed "]:
                continue
            item["opening_hours"].add_range(day, times[0].strip(), times[1].strip())

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
