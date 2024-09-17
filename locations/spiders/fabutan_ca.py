from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FabutanCASpider(SitemapSpider, StructuredDataSpider):
    name = "fabutan_ca"
    item_attributes = {"brand_wikidata": "Q120765494"}
    sitemap_urls = ["https://fabutan.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"/locations/[\w-]+/[\w-]+/[\w-]+/$",
            "parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Extract coordinates
        # <div style="background-image: url('https://maps.googleapis.com/maps/api/staticmap?center=49.273024,-122.789162&amp;size=640x640&amp;scale=1&amp;zoom=18&amp;maptype=roadmap&amp;key=AIzaSyBTwHa-5mEjikG0N8tP4aWr-FWp9QV1Sd8&amp;markers=icon:https%3a%2f%2ffabutan.com%3a443%2fimages%2fmap-icon.png%7C49.273024,-122.789162&amp;signature=F3g6mvzCMaG241atEo0LjRpriBQ=');"></div>
        background_map = (
            response.xpath('//div[contains(@style, "maps.googleapis.com")]/@style')
            .get()
            .split("staticmap?center=")[1]
            .split("&")[0]
        )
        item["lat"], item["lon"] = background_map.split(",")

        yield item
