from scrapy import Spider

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature


class SupaRoofZASpider(Spider):
    name = "supa_roof_za"
    start_urls = ["https://suparoof.co.za/store-locator/"]
    item_attributes = {
        "brand": "Supa-Roof",
        "brand_wikidata": "Q116474839",
    }

    def parse(self, response):
        for location in response.xpath('.//div[contains(@id, "suparoof-")]'):
            item = Feature()
            item["ref"] = location.xpath("./@id").get()
            item["branch"] = location.xpath(".//h3/strong/text()").get().replace("Supa-Roof", "").strip()
            item["addr_full"] = (
                location.xpath('string(.//i[contains(@class, "fa-address-card")]/../../..)').get().strip()
            )
            item["state"] = (
                location.xpath('../../../div[@class="panel-heading"]/.//div[@class="fusion-toggle-heading"]/text()')
                .get()
                .strip()
            )
            item["image"] = location.xpath('.//img[contains(@class, "img-responsive")]/@data-src').get()
            if maps_url := location.xpath('.//a[contains(@href, "google.com/maps")]/@href').get():
                item["lat"], item["lon"] = url_to_coords(maps_url)
            item["email"] = location.xpath('.//a[contains(@href, "mailto:")]/@href').get()
            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get()

            item["opening_hours"] = OpeningHours()
            hours_string = location.xpath('string(.//h3/strong[contains(text(), "Operating Hours")]/../../p)').get()
            hours_string = hours_string.replace("AM", "").replace("PM", "")
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
