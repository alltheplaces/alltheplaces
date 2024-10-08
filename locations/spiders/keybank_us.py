from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class KeybankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "keybank_us"
    item_attributes = {"brand": "KeyBank", "brand_wikidata": "Q1740314"}
    sitemap_urls = ["https://www.key.com/about/seo.sitemap-locator.xml"]
    sitemap_rules = [(r"locations/.*/.*/.*/.*", "parse_sd")]
    time_format = "%H:%M:%S"
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = response.css("h1.address__title::text").get()
        item.pop("image")
        item.pop("twitter")

        apply_category(Categories.BANK, item)
        if response.xpath(
            '//div[@class="info"]/h2[text()="Features & Services"]/following-sibling::ul/li[contains(text(), "ATM")]'
        ).get():
            apply_yes_no(Extras.ATM, item, True)

        yield item
