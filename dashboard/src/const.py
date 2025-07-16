ACCESS_TOKEN_URL = "https://app.hydrawise.com/api/v2/oauth/access-token"
API_URL = "https://app.hydrawise.com/api/v2/graph?appVersion=hydrawise-web-client"

CLIENT_SECRET = "zn3CrjglwNV1"
CLIENT_ID = "hydrawise_app"

PORT = 5253

GET_FLOW_DATA_QUERY = """
query getChartReportByType(
    $controllerId: Int!,
    $option: Int!,
    $startTime: Int,
    $endTime: Int,
    $type: ReportChartCategoryEnum!) {
  controller(controllerId: $controllerId) {
    id
    reporting(option: $option, startTime: $startTime, endTime: $endTime) {
      chartType(type: $type) {
        message
        title
        subtitle
        statistics
        xaxisArray
        yaxisArray
        xmin
        xmax
        ymin
        yaxis
        results
        __typename
      }
      __typename
    }
    zones {
        id
        name
    }
    __typename
  }
}
"""
