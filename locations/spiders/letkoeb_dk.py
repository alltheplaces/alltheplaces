import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class LetkoebDKSpider(SitemapSpider, StructuredDataSpider):
    name = "letkoeb_dk"
    item_attributes = {"brand": "Letkøb", "brand_wikidata": "Q67086705"}
    sitemap_urls = ["https://www.xn--letkb-yua.dk/letkob/sitemap.xml"]
    sitemap_rules = [(r"/butik/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, location=None, **kwargs):
        script_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        content = script_data["props"]["pageProps"]["content"]["entity"]["attributes"]
        if geo_data := content.get("field_location"):
            item["lat"] = geo_data.get("lat")
            item["lon"] = geo_data.get("lon")
        if address := content.get("field_address"):
            item["postcode"] = address.get("postal_code")
            item["city"] = address.get("locality")
            item["street_address"] = merge_address_lines([address["address_line1"], address["address_line2"]])

        item["email"] = content.get("field_store_email")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
