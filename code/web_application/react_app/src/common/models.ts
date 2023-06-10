import {} from "@chakra-ui/react";
import { ChartTypeRegistry } from "chart.js";

/**
 * Types for ChartJS component - ReactChartJS
 */
export interface ReactChartType {
  chartXAxis?: any;
  chartDatasets: any;
  chartOptions?: any;
  chartType: keyof ChartTypeRegistry;
}
