from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BhfGBSpider(SitemapSpider, StructuredDataSpider):
    name = "bhf_gb"
    item_attributes = {"brand": "British Heart Foundation", "brand_wikidata": "Q4970039"}
    sitemap_urls = ["https://www.bhf.org.uk/sitemap.xml"]
    sitemap_rules = [
        (r"/find-bhf-near-you/.*book-bank.*$", "parse"),
        (r"/find-bhf-near-you/.*clothing-bank.*$", "parse"),
        (r"/find-bhf-near-you/.+-shop.*", "parse"),
        (r"/find-bhf-near-you/.+-store.*", "parse"),
        (r"/find-bhf-near-you/.+-fashion-.*$", "parse"),
        (r"/find-bhf-near-you/.+-furniture-.*$", "parse"),
        (r"/find-bhf-near-you/stockbridge$", "parse"),
        (r"/find-bhf-near-you/pontefract$", "parse"),
    ]
    wanted_types = ["ClothingStore", "HomeGoodsStore"]
    drop_attributes = {"image"}

    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response):
        if "office" in response.url:
            return
        if "ld+json" in response.text:
            for item in self.parse_sd(response):
                extract_google_position(item, response)
                item["branch"] = item.pop("name")
        else:
            item = Feature()
            item["ref"] = response.url
            item["name"] = "British Heart Foundation"
            item["branch"] = response.xpath("//h1/text()").get()
            item["addr_full"] = response.xpath('//p[@class="highlighted-info-block__description"]/text()').get()
            item["lat"], item["lon"] = (
                response.xpath('//a[contains (@href,"www.google.com/maps/place/")]/@href')
                .get()
                .replace("https://www.google.com/maps/place/", "")
                .split(",")
            )
            item["opening_hours"] = OpeningHours()
            hours_string = (
                " ".join(response.xpath('//div[@class="opening-hours__days"]//text()').getall())
                .replace('<p class="opening-hours__description">', "")
                .replace("</p>", ";")
            )
            item["opening_hours"].add_ranges_from_string(hours_string)
            item["phone"] = response.xpath(
                '//div[@class="opening-hours__contact-us"]/p[@class="opening-hours__description"]/text()'
            ).get()
        if "permanently closed" in item["branch"]:
            return
        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)
        if "book-bank" in response.url:
            apply_category(Categories.RECYCLING, item)
            apply_yes_no("recycling:books", item, True)
        elif "clothing-bank" in response.url:
            apply_category(Categories.RECYCLING, item)
            apply_yes_no("recycling:clothes", item, True)
        elif "-bhf-shop" in response.url:
            apply_category(Categories.SHOP_CHARITY, item)
        elif "-home-" in response.url or "-furniture-" in response.url:
            apply_category(Categories.SHOP_FURNITURE, item)
        else:
            apply_category(Categories.SHOP_CHARITY, item)
        yield item
