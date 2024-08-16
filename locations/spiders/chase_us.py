from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class ChaseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "chase_us"
    item_attributes = {"brand": "Chase", "brand_wikidata": "Q524629"}
    allowed_domains = ["locator.chase.com"]
    sitemap_urls = ["https://locator.chase.com/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locator\.chase\.com\/(?!es)[a-z]{2}\/[\w\-]+\/[\w\-]+$", "parse_sd")]

    def extract_amenity_features(self, item, response, ld_data):
        # First, determine if we are a bank or ATM.
        hours_text = " ".join(
            response.xpath(
                '//div[contains(@class, "Core-branchRow--hours")]//table[1]/tbody/tr[@itemprop="openingHours"]/@content'
            ).getall()
        )

        atm_count = response.xpath('//div[@class="Core-atmCount"]/text()').get()
        if hours_text and atm_count:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        elif hours_text:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, False)
        elif atm_count:
            apply_category(Categories.ATM, item)
            # ATM specific tagging
            # Deposit ATM
            # Audio Assisted ATM
            if "amenityFeature" in ld_data:
                apply_yes_no("cash_in", item, "Deposit ATM" in ld_data["amenityFeature"], True)
                apply_yes_no("speech_output:en", item, "Audio Assisted ATM" in ld_data["amenityFeature"], True)

        if "amenityFeature" in ld_data:
            # Drive Up
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Up" in ld_data["amenityFeature"], True)

            # Cash Dispenser
            # Deposit Friendly

    def post_process_item(self, item, response, ld_data):
        item["ref"] = item["ref"].split("#", 1)[1]
        hours_text = " ".join(
            response.xpath(
                '//div[contains(@class, "Core-branchRow--hours")]//table[1]/tbody/tr[@itemprop="openingHours"]/@content'
            ).getall()
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text)
        item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        yield item
