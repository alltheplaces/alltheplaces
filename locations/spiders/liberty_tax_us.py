import json

from scrapy.spiders import SitemapSpider

from locations.categories import apply_yes_no
from locations.items import SocialMedia, set_closed, set_social_media
from locations.structured_data_spider import StructuredDataSpider


class LibertyTaxUSSpider(SitemapSpider, StructuredDataSpider):
    name = "liberty_tax_us"
    item_attributes = {
        "brand": "Liberty Tax",
        "brand_wikidata": "Q6541978",
    }
    sitemap_urls = ["https://www.libertytax.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://www.libertytax.com/income-tax-preparation-locations/[\w-]+/[\w-]+/(\d+)$", "parse"),
    ]
    search_for_image = False
    search_for_twitter = False
    drop_attributes = {"name"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if " - " in item["name"]:
            _, _, item["branch"] = item.pop("name").partition(" - ")

        if next_data := response.xpath("//script[@id='__NEXT_DATA__']/text()").get():
            office_data = json.loads(next_data).get("props", {}).get("pageProps", {}).get("officeData", {})
        else:
            office_data = None

        if office_data:
            if office_data["type"] == "VTO":
                return

            apply_yes_no("language:es", item, office_data["spanish"] == "true")
            if office_data["active"] != "true":
                set_closed(item)

            set_social_media(item, SocialMedia.LINKEDIN, office_data["socialMedia"].get("linkedin"))
            set_social_media(item, SocialMedia.PINTEREST, office_data["socialMedia"].get("pinterest"))
            set_social_media(item, SocialMedia.TWITTER, office_data["socialMedia"].get("twitter"))
            set_social_media(item, SocialMedia.YELP, office_data["socialMedia"].get("yelp"))

            item["lat"] = office_data.get("latitude")
            item["lon"] = office_data.get("longitude")
            if isinstance(item["lon"], float) and item["lon"] >= 0:
                item["lon"] = -item["lon"]

        yield item
