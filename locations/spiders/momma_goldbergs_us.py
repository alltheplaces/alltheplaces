from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MommaGoldbergsUSSpider(Spider):
    name = "momma_goldbergs_us"
    item_attributes = {"brand": "Momma Goldberg's Deli"}
    start_urls = ["https://mommagoldbergs.com/locations/"]
    custom_settings = {"DOWNLOAD_DELAY": 10, "DOWNLOAD_DELAY_JITTER": 0}

    def parse(self, response):
        yield from response.follow_all(css=".elementor-portfolio-item a", callback=self.parse_store)

    def parse_store(self, response):
        # Invalid closing br tags otherwise merge the address lines during HTML parsing.
        selector = Selector(text=response.text.replace("</br>", "<br>"))
        address = selector.xpath('//h2/a[contains(@href, "maps") or contains(@href, "goo.gl")]')
        item = Feature(
            ref=response.url.rstrip("/").rsplit("/", 1)[-1],
            branch=response.css("h1").xpath("normalize-space(.)").get(),
            addr_full=" ".join(address.xpath(".//text()").getall()),
            country="US",
            phone=response.css('a[href^="tel:"]::attr(href)').get(default="").removeprefix("tel:"),
            website=response.url,
        )
        hours = OpeningHours()
        for paragraph in response.xpath('//p[strong[contains(., "Hours")]]'):
            text = " ".join(paragraph.xpath(".//text()").getall()).replace("|", " ").replace(".", "")
            if "7 days a week" in text:
                text = "Mo-Su " + text.replace("7 days a week", "").replace("Hours", "")
            hours.add_ranges_from_string(text)
        item["opening_hours"] = hours
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"
        yield item
