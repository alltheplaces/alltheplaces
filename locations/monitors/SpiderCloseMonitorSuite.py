import spidermon.contrib.scrapy.monitors as stock_monitors
from spidermon import MonitorSuite
from spidermon.contrib.actions.sentry import SendSentryMessage
from spidermon.contrib.actions.slack.notifiers import SendSlackMessageSpiderFinished

from locations.monitors.HistoryMonitor import HistoryMonitor


class SpiderCloseMonitorSuite(MonitorSuite):
    monitors = [
        HistoryMonitor,
        stock_monitors.ItemCountMonitor,
        # stock_monitors.ItemValidationMonitor,
        stock_monitors.ErrorCountMonitor,
        stock_monitors.WarningCountMonitor,
        stock_monitors.FinishReasonMonitor,
        stock_monitors.UnwantedHTTPCodesMonitor,
        # stock_monitors.FieldCoverageMonitor,
        stock_monitors.RetryCountMonitor,
        stock_monitors.DownloaderExceptionMonitor,
        stock_monitors.SuccessfulRequestsMonitor,
        # stock_monitors.TotalRequestsMonitor,
    ]

    monitors_finished_actions = [
        SendSlackMessageSpiderFinished,
    ]

    monitors_failed_actions = [
        SendSentryMessage,
    ]
