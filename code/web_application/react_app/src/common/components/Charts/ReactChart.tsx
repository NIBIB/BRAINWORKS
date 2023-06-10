import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
  BarController,
  PieController,
  LineController,
  TimeScale,
} from "chart.js";
import { Chart } from "react-chartjs-2";
import { ReactChartType } from "../../models";
// @ts-ignore
import "chartjs-adapter-date-fns";

/**
 * React Chart
 *
 * React component which wraps React ChartJS, reducing boiler plate code for ChartJS
 */
const ReactChart = ({
  chartXAxis,
  chartDatasets,
  chartOptions,
  chartType,
}: ReactChartType) => {
  ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement,
    BarController,
    PieController,
    LineController,
    TimeScale
  );

  const reactChartOptions = chartOptions && { ...chartOptions };

  const barChartOptions = chartType === "bar" && {
    scales: {
      y: {
        ticks: {
          precision: 0,
        },
      },
    },
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    tooltips: {
      position: "nearest",
    },

    ...barChartOptions,
    ...reactChartOptions,
  };

  const labels = chartXAxis;

  const data = {
    labels,
    datasets: chartDatasets,
  };

  return <Chart type={chartType} options={options} data={data} />;
};

export default ReactChart;
