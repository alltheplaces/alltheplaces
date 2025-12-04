import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TudorsBiscuitWorldUSSpider(scrapy.Spider):
    name = "tudors_biscuit_world_us"
    start_urls = ["https://tudorsbiscuitworld.com/locations/"]
    item_attributes = {
        "brand": "Tudor's Biscuit World",
        "brand_wikidata": "Q7851262",
    }
    no_refs = True

    def parse(self, response):
        for loc in response.css(".card_locations"):
            item = Feature()
            item["branch"] = loc.xpath(".//h2/text()").get()
            (inner,) = loc.xpath("div[@class='card__expander_locations']")
            addr = inner.xpath(".//a[starts-with(@href, 'geo:')]")
            item["lat"], item["lon"] = addr[0].xpath("@href").get().removeprefix("geo:").split(",")
            if not item["lon"].startswith("-"):
                item["lon"] = "-" + item["lon"]
            item["addr_full"] = merge_address_lines([a.xpath(".//text()").get() for a in addr])
            item["street_address"] = addr[0].xpath(".//text()").get()
            item["phone"] = inner.xpath(".//a[starts-with(@href, 'tel:')]/@href").get().removeprefix("tel:")

            oh = OpeningHours()
            for line in inner.xpath(".//div[@class='container']/div[@class='row']"):
                oh.add_ranges_from_string(" ".join(line.xpath(".//text()").getall()))
            item["opening_hours"] = oh

            yield item
