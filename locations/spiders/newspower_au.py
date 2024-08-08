from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class NewspowerAUSpider(SitemapSpider):
    # Whilst WP Store Locator is used for this brand, it is set to
    # return at most the 5 closest points to a provided search
    # coordinate. There is an impractical number of search requests
    # thus required to use the WP Store Locator store finder API.
    # A Sitemap spider is used instead.
    name = "newspower_au"
    item_attributes = {"brand": "Newspower", "brand_wikidata": "Q120670137"}
    allowed_domains = ["newspower.com.au"]
    sitemap_urls = [
        "https://newspower.com.au/wpsl_stores-sitemap1.xml",
        "https://newspower.com.au/wpsl_stores-sitemap2.xml",
    ]
    sitemap_rules = [(r"^https:\/\/newspower\.com\.au\/stores/[^/]+\/$", "parse")]
    # Server will redirect wpsl_stores-sitemap2.xml to
    # https://newspower.com.au/store-locator/ if it doesn't like
    # the country/netblock requesting the page.
    requires_proxy = True

    def parse(self, response):
        map_marker_js_blob = response.xpath('//script[contains(text(), "var wpslMap_0 = ")]/text()').get()
        map_marker_js_blob = map_marker_js_blob.split("var wpslMap_0 = ", 1)[1].split("]};", 1)[0] + "]}"
        map_marker_dict = parse_js_object(map_marker_js_blob)["locations"][0]
        properties = {
            "ref": map_marker_dict["id"],
            "name": response.xpath('//div[@class="wpsl-locations-details"]/span/strong/text()').get().strip(),
            "addr_full": clean_address(response.xpath('//div[@class="wpsl-location-address"]//text()').getall()),
            "street_address": clean_address([map_marker_dict["address"], map_marker_dict["address2"]]),
            "city": map_marker_dict["city"],
            "state": map_marker_dict["state"],
            "postcode": map_marker_dict["zip"],
            "lat": map_marker_dict["lat"],
            "lon": map_marker_dict["lng"],
            "phone": response.xpath('//div[@class="wpsl-contact-details"]//a[contains(@href, "tel:")]/@href').get(),
            "website": response.url,
            "facebook": response.xpath(
                '//div[@class="entry-content"]//a[contains(@href, "https://www.facebook.com/")]/@href'
            ).get(),
        }
        if properties.get("phone") and "tel:" in properties.get("phone"):
            properties["phone"] = properties["phone"].replace("tel:", "")
        hours_string = " ".join(filter(None, response.xpath('//table[@class="wpsl-opening-hours"]//text()').getall()))
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
