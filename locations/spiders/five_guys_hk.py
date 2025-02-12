from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysHKSpider(FiveGuysAUSpider):
    name = "five_guys_hk"
    experience_key = "search-backend-hk"
    locale = "en-HK"  # Using en because it has google attributes which gives lots of extra details (not present in zh-Hans-HK)

    def process_websites(self, item) -> None:
        item["extras"]["website:en"] = item["website"]
        item["extras"]["website:zh"] = item["website"].replace("/en_hk/", "/")
        item["website"] = item["extras"]["website:zh"]
