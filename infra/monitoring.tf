resource "google_monitoring_dashboard" "calendar_service" {
  dashboard_json = jsonencode({
    displayName = "Calendar Client Service"
    mosaicLayout = {
      columns = 12
      tiles = [
        # ---- Tile 1: Request Latency Heatmap ----
        {
          width  = 6
          height = 4
          widget = {
            title = "Request Latency (ms) by Route"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"workload.googleapis.com/custom.googleapis.com/http/request_latency\" resource.type=\"generic_node\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_99"
                      groupByFields      = ["metric.labels.route"]
                    }
                  }
                }
                plotType   = "LINE"
                legendTemplate = "p99 $${metric.labels.route}"
              }]
              yAxis = { label = "Latency (ms)", scale = "LINEAR" }
            }
          }
        },
        # ---- Tile 2: Request Count by Status Category ----
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Request Count by Status Category"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"workload.googleapis.com/custom.googleapis.com/http/request_count\" resource.type=\"generic_node\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["metric.labels.status_category"]
                    }
                  }
                }
                plotType = "STACKED_BAR"
                legendTemplate = "$${metric.labels.status_category}"
              }]
              yAxis = { label = "Requests/sec", scale = "LINEAR" }
            }
          }
        },
        # ---- Tile 3: Success Rate Gauge ----
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Success Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"workload.googleapis.com/custom.googleapis.com/http/success_rate\" resource.type=\"generic_node\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
                legendTemplate = "Success Rate"
              }]
              yAxis = { label = "Rate (0-1)", scale = "LINEAR" }
            }
          }
        },
        # ---- Tile 4: Error Rate Breakdown ----
        {
          xPos   = 6
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Error Rate (Domain vs Infrastructure)"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"workload.googleapis.com/custom.googleapis.com/http/request_count\" resource.type=\"generic_node\" metric.labels.status_category!=\"success\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["metric.labels.status_category", "metric.labels.route"]
                    }
                  }
                }
                plotType = "LINE"
                legendTemplate = "$${metric.labels.status_category} - $${metric.labels.route}"
              }]
              yAxis = { label = "Errors/sec", scale = "LINEAR" }
            }
          }
        }
      ]
    }
  })
}