from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


# italtile_bw_za, topt_za and ctm all use a very similar storefinder
class CtmSpider(Spider):
    name = "ctm"
    allowed_domains = ["www.ctm.co.za"]
    start_urls = ["https://www.ctm.co.za/storefinder/"]
    item_attributes = {
        "brand": "CTM",
        "brand_wikidata": "Q127378361",
    }

    def parse(self, response):
        for country in response.xpath('.//div[@class="accordion"]'):
            country_name = country.xpath(".//h3/text()").get().strip()
            for province in country.xpath('.//div[@class="accordion__province row"]'):
                province_name = province.xpath(".//h6/text()").get().strip()
                for link in province.xpath('.//a[contains(@href, "/storefinder/")]/@href').getall():
                    yield Request(
                        url="https://www.ctm.co.za" + link,
                        meta={"country": country_name, "province": province_name},
                        callback=self.parse_store,
                    )

    def parse_store(self, response):
        item = Feature()

        coords = parse_js_object(
            response.xpath('.//script[contains(text(), "let position =")]/text()').get().split("let position =")[1]
        )
        item["lat"] = coords["lat"]
        item["lon"] = coords["lng"]

        item["website"] = response.url
        item["ref"] = response.url
        item["branch"] = response.xpath(".//h1/text()").get().replace("CTM", "").strip()

        item["addr_full"] = response.xpath('.//div[@class="details__info__location"]/h4/text()').get().strip()
        item["state"] = response.meta["province"]
        item["country"] = response.meta["country"]

        extract_phone(item, response.xpath('.//div[@class="details__info__text text--contact"]'))
        extract_email(item, response.xpath('.//div[@class="details__info__text text--contact"]'))

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            response.xpath('string(.//div[@class="details__info__text text--hours"])').get()
        )

        yield item
