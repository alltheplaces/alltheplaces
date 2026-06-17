import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class JyhJpSpider(SitemapSpider):
    name = "jyh_jp"
    item_attributes = {"brand": "Japan Youth Hostel", "brand_wikidata": "Q11441965", "country": "JP"}
    sitemap_urls = ["https://jyh.jp/sitemap.xml"]
    sitemap_rules = [(r"/info\.php\?jyhno=\d+$", "parse")]

    def parse(self, response: Response, **kwargs):
        # Extract name (format: "日本語名 / English Name")
        name_raw = response.xpath('//h3[@class="oomidashi"]/text()').getall()
        name_text = " ".join(t.strip() for t in name_raw if t.strip())
        # Split on " / " to get both Japanese and English names
        if " / " in name_text:
            name_ja, name_en = name_text.split(" / ", 1)
        else:
            name_ja = name_text
            name_en = None

        # Extract coordinates from Google Maps iframe
        coords = re.search(r"maps\.google[^\"']*[?&]q=([0-9.\-]+),([0-9.\-]+)", response.text)
        if not coords:
            return
        lat, lon = float(coords.group(1)), float(coords.group(2))

        # Extract postcode and address
        addr_block = re.search(
            r"住所<br><span class=\"item_price2\">(.*?)</span>", response.text, re.DOTALL
        )
        postcode = None
        street_address = None
        if addr_block:
            raw = re.sub(r"<[^>]+>", "", addr_block.group(1)).strip()
            lines = [line.strip() for line in raw.splitlines() if line.strip()]
            for line in lines:
                # Japanese postal code starts with 〒
                pc = re.match(r"[〒](\d{3}-\d{4})", line)
                if pc:
                    postcode = pc.group(1)
                else:
                    street_address = line

        # Extract phone number
        phone_match = re.search(r"電話番号.*?<span class=\"item_price2\">([\d\-]+)</span>", response.text, re.DOTALL)
        phone = phone_match.group(1).strip() if phone_match else None

        # Use jyhno as stable ref
        ref_match = re.search(r"jyhno=(\d+)", response.url)
        ref = ref_match.group(1) if ref_match else response.url

        item = Feature()
        item["ref"] = ref
        item["name"] = name_en or name_ja
        item["extras"]["name:ja"] = name_ja
        item["lat"] = lat
        item["lon"] = lon
        item["postcode"] = postcode
        item["street_address"] = street_address
        item["phone"] = phone
        item["website"] = response.url

        apply_category(Categories.TOURISM_HOSTEL, item)

        yield item
