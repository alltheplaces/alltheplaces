from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysCHSpider(FiveGuysAUSpider):
    name = "five_guys_ch"
    experience_key = "search-backend-ch"
    locale = (
        "en-CH"  # Using en because it has google attributes which gives lots of extra details (not present in de or fr)
    )

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:de"] = item["website"].replace("/en_ch/", "/")
        item["extras"]["website:fr"] = item["website"].replace("/en_ch/", "/fr_ch/")
        item["website"] = item["extras"]["website:de"]
