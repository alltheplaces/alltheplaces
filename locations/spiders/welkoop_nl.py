import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class WelkoopNLSpider(SitemapSpider):
    name = "welkoop_nl"
    item_attributes = {"brand": "Welkoop", "brand_wikidata": "Q72799253"}
    sitemap_urls = ["https://www.welkoop.nl/sitemap/sitemap_dealers1.xml"]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h2/text()").get().replace("Welkoop ", "")
        item["lat"] = re.search(r"DealerDetail\.lat.*?(-?\d+\.\d+);", response.text).group(1)
        item["lon"] = re.search(r"DealerDetail\.lng.*?(-?\d+\.\d+);", response.text).group(1)
        item["addr_full"] = re.search(r"DealerDetail\.destination.*\'(.*)\';", response.text).groups()
        item["ref"] = item["website"] = response.url
        item["opening_hours"] = OpeningHours()
        day_time = re.findall(
            r"([a-zA-Z]+)(\d+:\d+)\s*tot\s*(\d+:\d+)",
            response.xpath('//*[@id="datawrapper"]//*[@class="columns six"][1]').xpath("normalize-space()").get(),
        )
        for time_details in day_time:
            day, open_time, close_time = time_details
            item["opening_hours"].add_range(day=sanitise_day(day, DAYS_NL), open_time=open_time, close_time=close_time)
        apply_category(Categories.SHOP_GARDEN_CENTRE, item)
        yield item
