from spidermon import Monitor, MonitorSuite, monitors


@monitors.name("History Validation")
class HistoryMonitor(Monitor):
    @monitors.name("Expected number of items extracted")
    def test_expected_number_of_items_extracted(self):
        spider = self.data["spider"]
        total_previous_jobs = len(spider.stats_history)
        if total_previous_jobs == 0:
            return

        previous_item_extracted_mean = (
            sum(previous_job["item_scraped_count"] for previous_job in spider.stats_history)
            / total_previous_jobs
        )
        items_extracted = self.data.stats["item_scraped_count"]

        # Minimum number of items we expect to be extracted
        minimum_threshold = 0.9 * previous_item_extracted_mean

        self.assertFalse(
            items_extracted <= minimum_threshold,
            msg="Expected at least {} items extracted.".format(minimum_threshold),
        )
