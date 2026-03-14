import html

from scrapy.crawler import Crawler

from locations.items import Feature


def clean_string(val: str) -> str:
    return html.unescape(val).strip().replace("\u200b", "")


class CleanStringsPipeline:
    crawler: Crawler

    skipped_keys = {"nsi_id", "twitter", "facebook"}
    url_keys = {"ref", "website", "image"}

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:
        for key, value in item.items():
            if not isinstance(value, str):
                continue

            if key in self.skipped_keys:
                continue

            if key in self.url_keys:
                cleaned_value = value.strip()
                if cleaned_value != value:
                    item[key] = cleaned_value
                    if self.crawler.stats:
                        self.crawler.stats.inc_value("atp/clean_strings/{}".format(key))
            else:
                cleaned_value = clean_string(value)
                if cleaned_value != value:
                    item[key] = cleaned_value
                    if self.crawler.stats:
                        self.crawler.stats.inc_value("atp/clean_strings/{}".format(key))

        return item
