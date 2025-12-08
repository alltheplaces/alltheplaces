from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class VanSchaikBWNAZASpider(Spider):
    name = "van_schaik_bw_na_za"
    start_urls = ["https://www.vanschaik.com/find-store"]
    item_attributes = {
        "brand": "Van Schaik",
        "brand_wikidata": "Q116741158",
    }

    def parse(self, response):
        for location in response.xpath('.//div[@class="row allaccordions"]/.//div[@class="card"]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["branch"] = location.xpath('.//div[@class="card-header"]/text()').get().strip()
            item["addr_full"] = clean_address(location.xpath(".//address/text()").getall())
            item["state"] = location.xpath("../.././/h2/text()").get().strip()
            if item["state"] in ["Botswana", "Namibia"]:
                item["country"] = item.pop("state")
            else:
                item["country"] = "ZA"
            item["phone"] = location.xpath('.//strong[contains(text(), "Phone:")]/../a/@href').get()
            if item["phone"] is not None and "/" in item["phone"]:
                phones = [phone.strip() for phone in item["phone"].split("/")]
                item["phone"] = phones[0]
                for phone in phones[1:]:
                    if len(phone) <= 4:
                        item["phone"] += "; " + phones[0][: -len(phone)] + phone
                    else:
                        item["phone"] += "; " + phone
            item["extras"]["fax"] = location.xpath('.//strong[contains(text(), "Fax:")]/../a/@href').get()
            item["email"] = location.xpath('.//a[contains(@href, "mailto:")]/@href').get()

            item["opening_hours"] = OpeningHours()
            for line in location.xpath('.//div[@class="card-body"]/li/text()').getall():
                item["opening_hours"].add_ranges_from_string(line)

            yield item
