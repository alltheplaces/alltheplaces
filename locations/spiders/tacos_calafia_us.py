from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TacosCalafiaUSSpider(Spider):
    name = "tacos_calafia_us"
    item_attributes = {"brand": "Tacos Calafia"}
    start_urls = ["https://tacoscalafia.com/"]

    def parse(self, response):
        for card in response.css(".fl-module-info-box[id]"):
            address = card.css(".uabb-infobox-text > p:first-child::text").getall()
            if len(address) != 2:
                continue
            city, state, postcode = address[1].rsplit(None, 2)
            item = Feature(
                # The HTML id "downtown" is reused by five location cards.
                ref=card.attrib["data-node"],
                branch=card.css(".uabb-infobox-title::text").get(),
                street_address=address[0].strip(),
                city=city.rstrip(","),
                state=state,
                postcode=postcode,
                country="US",
                website=response.url,
            )
            hours = OpeningHours()
            for line in card.css(".uabb-infobox-text > p:not(:first-child)").xpath(".//text()").getall():
                if ":" in line and "closed" in line.lower():
                    hours.set_closed(line.split(":", 1)[0])
                else:
                    hours.add_ranges_from_string(line.replace("&", "and"))
            item["opening_hours"] = hours
            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "mexican"
            yield item
