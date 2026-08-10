import html

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class HostellingScotlandSpider(Spider):
    name = "hostelling_scotland"
    item_attributes = {"brand": "Hostelling Scotland", "brand_wikidata": "Q7438052", "country": "GB"}
    start_urls = ["https://www.hostellingscotland.org.uk/inspiration/view-all-hostels/"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def parse(self, response: Response, **kwargs):
        data_raw = response.xpath('//input[@id="data"]/@value').get("")
        data_raw = html.unescape(data_raw)
        for record in data_raw.split("::"):
            if not record.strip():
                continue
            parts = record.split(",")
            if len(parts) < 5:
                continue
            name = parts[0].strip().strip('"')
            try:
                lat = float(parts[1].strip())
                lon = float(parts[2].strip())
            except (ValueError, IndexError):
                continue
            slug = parts[4].strip().strip('"')
            url = response.urljoin(slug)
            yield response.follow(
                url,
                callback=self.parse_hostel,
                meta={"name": name, "lat": lat, "lon": lon},
            )

    def parse_hostel(self, response: Response, **kwargs):
        item = Feature()
        item["branch"] = response.meta["name"]
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        item["website"] = response.url
        item["ref"] = response.url
        item.update(self.item_attributes)

        # Address: first icon-text__content block contains address spans
        # Format: span[0] = "street, city" (may have multiple comma parts), span[1] = postcode
        content_blocks = response.css(".icon-text__content")
        if content_blocks:
            spans = content_blocks[0].css("span::text").getall()
            if len(spans) >= 2:
                addr_city = spans[0].strip()
                if "," in addr_city:
                    street, _, city = addr_city.rpartition(",")
                    item["street_address"] = street.strip()
                    item["city"] = city.strip()
                else:
                    item["city"] = addr_city
                item["postcode"] = spans[1].strip()

        # Phone: href="tel:..." (HTML entity encoded)
        phone_href = response.xpath('//a[starts-with(@href, "tel:")]/@href').get("")
        if phone_href:
            phone = html.unescape(phone_href[4:]).strip()
            if phone:
                item["phone"] = phone

        # Email
        email_href = response.xpath('//a[starts-with(@href, "mailto:")]/@href').get("")
        if email_href:
            item["email"] = email_href[7:].strip()

        apply_category(Categories.TOURISM_HOSTEL, item)
        yield item
