import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class SparBESpider(scrapy.Spider):
    name = "spar_be"
    allowed_domains = ["www.spar.be"]
    start_urls = ["https://www.spar.be/winkels"]
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}

    def parse(self, response, **kwargs):
        result = response.xpath("//*[@id][@data-lat]")
        for x in range(0, len(result), 2):
            yield response.follow(
                url=result[x].xpath(".//a/@href").get(),
                callback=self.parse_item,
                cb_kwargs={"lat": result[x].xpath("./@data-lat").get(), "lon": result[x].xpath("./@data-lng").get()},
            )

    def parse_item(self, response, lat, lon, **kwargs):
        item = Feature()
        item["lat"] = lat
        item["lon"] = lon
        item["name"] = response.xpath(r"/html/head/title/text()").get().replace("| Spar", "").strip()
        item["addr_full"] = response.xpath('//*[@class="group-wrapper-address"]//*[@class="field__item"]/text()').get()

        item["ref"] = item["website"] = response.url

        if phone := response.xpath(r'//a[contains(@href, "tel:")]/@href/text()').get():
            item["phone"] = phone.replace("/", "").replace(";", "")

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//tr[contains(@class, "office-hours__item")]'):
            day = sanitise_day(rule.xpath(r'./td[@class="office-hours__item-label"]/text()').get(), DAYS_NL)
            time = rule.xpath('./td[@class="office-hours__item-slots"]/text()').get()
            if "Closed" in time:
                item["opening_hours"].set_closed(day)
            else:
                for period in time.split(","):
                    open_time, close_time = period.split("-")
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip())

        if item["name"].startswith("SPAR Express"):
            item["branch"] = item.pop("name").removeprefix("SPAR Express ")
            item["name"] = "Spar Express"
        else:
            item["branch"] = item.pop("name").removeprefix("SPAR ")
            item["name"] = "Spar"

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
