import re

from scrapy import Spider

from locations.items import Feature


class AristocrazySpider(Spider):
    name = "aristocrazy"
    item_attributes = {"brand": "Aristocrazy", "brand_wikidata": "Q117802848"}
    start_urls = ["https://www.aristocrazy.com/en/pages/aristocrazy-stores"]
    requires_proxy = True

    def parse(self, response):
        for store_list in response.css(".accordion__content"):
            for store_ul in store_list.css("ul"):
                # Store name may be in a <strong> inside a <li>, or in a preceding <p>
                name = store_ul.css("strong::text").get()
                if not name:
                    # Look for nearest preceding <p> sibling that contains a <strong>
                    name = store_ul.xpath("preceding-sibling::p[strong][1]/strong/text()").get()
                if not name:
                    continue
                name = name.strip()

                item = Feature()
                item["ref"] = re.sub(r"\W+", "-", name.lower())
                item["name"] = name
                item["website"] = "https://www.aristocrazy.com/en/pages/aristocrazy-stores"

                phone_el = store_ul.css("a[href^='tel:']")
                if phone_el:
                    item["phone"] = phone_el.attrib["href"].removeprefix("tel:")

                # Collect non-phone, non-name <li> text lines
                address_lines = []
                location_line = None
                for li in store_ul.css("li"):
                    if li.css("a[href^='tel:']") or li.css("strong"):
                        continue
                    text = " ".join(li.css("::text").getall()).strip()
                    if not text:
                        continue
                    if location_line is not None:
                        address_lines.append(location_line)
                    location_line = text

                if location_line:
                    parts = [p.strip() for p in location_line.split(",")]
                    if len(parts) >= 3 and re.match(r"[\d-]+", parts[0]):
                        item["postcode"] = parts[0]
                        item["city"] = parts[1]
                        item["country"] = parts[-1]
                    elif len(parts) == 2:
                        # Handle "AD500 Andorra la Vella, Andorra" pattern
                        postcode_match = re.match(r"([\w\d]+-?[\d]+)\s+(.+)", parts[0])
                        if postcode_match:
                            item["postcode"] = postcode_match.group(1)
                            item["city"] = postcode_match.group(2)
                        else:
                            item["city"] = parts[0]
                        item["country"] = parts[1]
                    else:
                        address_lines.append(location_line)

                if address_lines:
                    item["street_address"] = ", ".join(address_lines)

                yield item
