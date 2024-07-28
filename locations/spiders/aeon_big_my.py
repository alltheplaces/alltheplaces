from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AeonBigMYSpider(CrawlSpider):
    name = "aeon_big_my"
    item_attributes = {"brand": "AEON BiG", "brand_wikidata": "Q8077280", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["aeonbig.com.my"]
    start_urls = [
        "https://aeonbig.com.my/wp-content/themes/twentyseventeen/ajax/portfolio-ajax-load-more-store.php?limit=1000&id=&p=1"
    ]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/aeonbig\.com\.my\/store\/\?[\w\-]+$"), callback="parse")]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//h4[contains(@class, "heading-primarys")]/text()')
            .get("")
            .replace("AEON BiG ", ""),
            "addr_full": merge_address_lines(response.xpath('//div[@class="store_info"]/ul[1]/li[1]/text()').getall()),
            "phone": response.xpath('//div[@class="store_info"]/ul[1]/li[2]/text()').get("").strip(),
            "website": response.url,
            "opening_hours": OpeningHours(),
        }
        extract_google_position(properties, response)
        hours_string = " ".join(filter(None, map(str.strip, response.xpath('//li[@class="bs_date"]//text()').getall())))
        hours_string = hours_string.replace("Daily", "Mo-Su").replace("Weekday", "Mo-Fr").replace("Weekend", "Sa-Su")
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
