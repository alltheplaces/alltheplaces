import datetime

from scrapy import Selector
from scrapy.spiders import XMLFeedSpider
from scrapy.utils.spider import iterate_spider_output

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


def set_closed_missing_days(oph):
    for day in DAYS:
        if oph.day_hours.get(day, None):
            pass
        else:
            oph.days_closed.add(day)


class SinsaySpider(XMLFeedSpider):
    name = "sinsay"
    allowed_domains = ["www.sinsay.com"]
    start_urls = [f"https://www.sinsay.com/it/it/new_kml/sinsay_stores_en_{datetime.datetime.now():%Y%m%d}.kml"]
    iterator = "xml"
    itertag = "Placemark"
    item_attributes = {
        "brand": "Sinsay",
        "brand_wikidata": "Q107410579",
    }
    no_refs = True  # ids are just the order in response

    def parse_nodes(self, response, nodes):
        selector = Selector(
            text=response.body.decode().replace('xmlns="http://www.opengis.net/kml/2.2"', ""), type="xml"
        )
        nodes = selector.xpath("//Placemark")
        for selector in nodes:
            ret = iterate_spider_output(self.parse_node(response, selector))
            yield from self.process_results(response, ret)

    def parse_node(self, response, selector):
        item = Feature()
        apply_category(Categories.SHOP_CLOTHES, item)
        item["branch"] = selector.xpath("name/text()").get().removeprefix("SINSAY").strip()
        item["lon"], item["lat"], _ = selector.xpath("Point/coordinates/text()").get().split(",")
        description = Selector(text=selector.xpath("description/text()").get())
        ps = description.xpath("//p/text()")
        item["addr_full"] = ps[0:3].getall()
        item["city"] = ps[1].get()
        if phone := ps[3].get().replace("tel. ", ""):
            item["phone"] = phone
        item["opening_hours"] = oh = OpeningHours()
        oh.add_ranges_from_string(", ".join(ps[4:].getall()))
        set_closed_missing_days(oh)
        return item
