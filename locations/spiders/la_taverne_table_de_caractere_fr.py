from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, OpeningHours
from locations.items import Feature


class LaTaverneTableDeCaractereFRSpider(Spider):
    name = "la_taverne_table_de_caractere_fr"
    item_attributes = {"brand": "La Taverne - Table de Caractère", "brand_wikidata": "Q141215923"}
    allowed_domains = ["lestavernes.com"]
    start_urls = ["https://www.lestavernes.com/nos-restaurants-la-taverne-table-de-caracteres/"]

    def parse(self, response, **kwargs):
        for li in response.xpath('//ul[contains(@class, "wpv-loop")]/li'):
            marker = li.xpath('preceding-sibling::div[contains(@class, "js-wpv-addon-maps-marker")][1]')
            website = li.xpath(".//a/@href").get()

            item = Feature()
            item["ref"] = website.strip("/").rsplit("/", 1)[-1]
            item["website"] = website
            item["branch"] = li.xpath('.//div[@class="nom-restaurant"]/text()').get("").strip()
            item["street_address"] = li.xpath('.//div[@class="adresse-restaurant"]/text()').get("").strip()
            item["postcode"] = li.xpath('.//div[@class="code_postal-restaurant"]/text()').get("").strip()
            item["city"] = (
                li.xpath('.//div[@class="code_postal-restaurant"]/following-sibling::div/text()').get("").strip()
            )
            item["phone"] = li.xpath('.//div[@class="tel-restaurant"]/text()').get()
            item["email"] = li.xpath('.//div[@class="mail-restaurant"]//a/@href').get("").replace("mailto:", "")
            item["lat"] = marker.xpath("@data-markerlat").get()
            item["lon"] = marker.xpath("@data-markerlon").get()

            # A couple of locations have the postcode merged into the city field on the source page.
            if item["city"][:5].isdigit():
                item["postcode"], item["city"] = item["city"][:5], item["city"][5:].strip()

            apply_category(Categories.RESTAURANT, item)

            yield response.follow(website, callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response, item):
        # Opening hours live on the restaurant page as a column of Elementor heading widgets (day names)
        # each followed by two "shortcode" widgets holding either a "HHhMM - HHhMM" range, a bare "HHhMM"
        # time (a single continuous range split into an open and a close value), or "Fermé".
        oh = OpeningHours()
        for heading in response.xpath('//h5[contains(@class, "elementor-heading-title")]'):
            day = heading.xpath("normalize-space(.)").get()
            if day not in DAYS_FR:
                continue
            day = DAYS_FR[day]

            slots = heading.xpath(
                'ancestor::div[contains(@class, "elementor-widget-heading")]'
                '/following-sibling::div[contains(@class, "elementor-widget-shortcode")][position() <= 2]'
                '//div[contains(@class, "elementor-shortcode")]/text()'
            ).getall()
            slots = [slot.strip() for slot in slots if slot.strip()]
            if slots and all(slot.lower() in CLOSED_FR for slot in slots):
                oh.set_closed(day)
                continue

            bare = []
            for slot in slots:
                if slot.lower() in CLOSED_FR:
                    continue
                if "-" in slot:
                    start, end = slot.split("-", 1)
                    oh.add_range(day, self.clean_time(start), self.clean_time(end), closed=CLOSED_FR)
                else:
                    bare.append(self.clean_time(slot))
            if len(bare) == 2:
                oh.add_range(day, bare[0], bare[1], closed=CLOSED_FR)

        item["opening_hours"] = oh
        yield item

    @staticmethod
    def clean_time(value):
        return value.strip().lower().replace("h", ":")
