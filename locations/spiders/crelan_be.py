from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class CrelanBESpider(SitemapSpider):
    name = "crelan_be"
    item_attributes = {"brand": "Crelan", "brand_wikidata": "Q389872"}
    start_urls = ["https://www.crelan.be/nl/particulieren/json/agencies"]
    sitemap_urls = ["https://www.crelan.be/sitemap.xml"]
    sitemap_rules = [(r"https://www.crelan.be/nl/kantoor/[a-z-0-9]+$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["street_address"] = response.xpath(
            '//*[@class="address-display-element address-line1-element"]/text()'
        ).get()
        item["postcode"] = response.xpath('//*[@class= "address-display-element postal-code-element"]/text()').get()
        item["city"] = response.xpath('//*[@class="address-display-element locality-element"]/text()').get()
        if phone := response.xpath('//*[contains(@href,"tel:")]'):
            item["phone"] = phone.xpath(".//@href").get().replace("tel:", "")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.BANK, item)
        apply_yes_no(
            Extras.ATM, item, "Geldautomaat" in response.xpath('//*[@class="agency-teaser__contact"]/li//text()').get()
        )
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="box agency-detail__opening-hours-tabular"]//table//tr'):
            day = sanitise_day(day_time.xpath("./td[1]/text()").get(), DAYS_NL)
            time = day_time.xpath("./td[2]/text()").getall()
            if time is None:
                continue
            for open_close_time in time:
                open_time, close_time = open_close_time.replace("(op afspraak)", "").split("-")
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
