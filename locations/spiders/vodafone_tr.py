import scrapy
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_TR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.vodafone_de import VODAFONE_SHARED_ATTRIBUTES


class VodafoneTRSpider(scrapy.Spider):
    name = "vodafone_tr"
    item_attributes = VODAFONE_SHARED_ATTRIBUTES
    start_urls = ["https://www.vodafone.com.tr/bayi"]
    link_extractor = LinkExtractor(allow=r"/bayi/\w+/\w+/\w+", restrict_xpaths=r'//*[@id="js-stores"]//a')

    def parse(self, response, **kwargs):
        for state in response.xpath(r'//*[@id="cities"]/option'):
            state_id = state.xpath("./@value").get()
            state_name = state.xpath("./text()").get()
            yield scrapy.Request(
                url=f"https://www.vodafone.com.tr/api/lead_form/getRegions?city_id={state_id}",
                cb_kwargs={"state": state_name},
                callback=self.parse_city,
            )

    def parse_city(self, response, **kwargs):
        for city in response.json():
            city_url = "https://www.vodafone.com.tr/" + city["seo"]
            city_name = city["name"]
            yield scrapy.Request(
                url=city_url, callback=self.parse_poi_url, cb_kwargs={"state": kwargs["state"], "city": city_name}
            )

    def parse_poi_url(self, response, **kwargs):
        for links in self.link_extractor.extract_links(response):
            yield scrapy.Request(
                url=links.url, callback=self.parse_details, cb_kwargs={"state": kwargs["state"], "city": kwargs["city"]}
            )

    def parse_details(self, response, **kwargs):
        item = Feature()
        item["addr_full"] = response.xpath(r'//*[contains(@class, "address")]/text()').get()
        item["state"] = kwargs["state"]
        item["city"] = kwargs["city"]
        item["phone"] = response.xpath(r'//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath(r'//*[contains(@class,"dd-time my-1")]'):
            day = sanitise_day(day_time.xpath("./b/text()").get(), DAYS_TR)
            if day is not None:
                open_time, close_time = day_time.xpath("./text()").get().split("-")
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
