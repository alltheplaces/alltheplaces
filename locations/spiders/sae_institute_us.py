from locations.spiders.sae_institute_au import SaeInstitueAUSpider


class SaeInstituteUSSpider(SaeInstitueAUSpider):
    name = "sae_institute_us"
    start_urls = ["https://usa.sae.edu/contact-us/"]

    def post_process_item(self, item, response, location):
        item["phone"] = location.xpath('.//a[contains(@href, "tel")]/@href').get()
        item["name"] = item.pop("branch")
        yield item
