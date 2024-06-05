from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KwikKopyAUSpider(CrawlSpider, StructuredDataSpider):
    name = "kwik_kopy_au"
    item_attributes = {"brand": "Kwik Kopy", "brand_wikidata": "Q126168253", "extras": Categories.SHOP_COPYSHOP.value}
    allowed_domains = ["www.kwikkopy.com.au"]
    start_urls = ["https://www.kwikkopy.com.au/browse-centres"]
    rules = [Rule(LinkExtractor(r"^https:\/\/www\.kwikkopy\.com\.au\/browse-centres\/[\w\-]+$"), "parse_sd")]
    download_delay = 0.2

    def post_process_item(self, item, response, ld_data):
        item["lat"] = response.xpath('//div[@class="gmap"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@class="gmap"]/@data-lng').get()
        if not item["lat"] or not item["lon"]:
            # Locations without coordinates were found to be closed.
            return

        item["branch"] = item["name"].replace("Kwik Kopy ", "")
        item["addr_full"] = item.pop("street_address", None)
        item.pop("image", None)  # data:image/png;base64 should be ignored.
        item.pop("facebook", None)  # Brand Facebook page, not location specific.

        hours_string = " ".join(
            filter(
                None,
                map(
                    str.strip,
                    response.xpath('//div[contains(@class, "store-information")]/div[4]/span/text()').getall(),
                ),
            )
        )
        hours_string = (
            hours_string.replace(" (other times by appointment)", "")
            .replace(", with after hours pick up on request", "")
            .replace("(until 5:30pm by appointment only)", "")
            .replace("Fridays", "Friday")
        )
        if "Monday" in hours_string and not hours_string.startswith("Monday"):
            # If "Monday" is included after offset 0 in the string, the string
            # needs to be reordered so the day range is first and hours range
            # second.
            hours_string = "Monday" + hours_string.split(" Monday", 1)[1] + ": " + hours_string.split(" Monday", 1)[0]
        elif "Monday" not in hours_string:
            # If "Monday" is not included, the location is assumed to be open
            # Monday-Friday. The hours string is believed to just be lazily
            # truncated to remove any mention of days of the week the loation
            # is open.
            hours_string = "Monday - Friday: " + hours_string
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)

        yield item
