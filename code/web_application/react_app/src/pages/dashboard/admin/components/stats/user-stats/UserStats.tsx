import { SimpleGrid } from "@chakra-ui/react";
import useAxios from "axios-hooks";
import { API_URL } from "../../../../../../common/templates/api";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

import {
  brand300a,
  brand400,
  greenGenA,
  redGenA,
  yellowGenA,
} from "../../../../../../setup/theme/colors";
import ReactChartCard from "../../../../../../common/components/Charts/ReactChartCard";
import { getPallete } from "../../../../../../setup/theme/utils";

export interface ChartDataType {
  name: string;
  value: number;
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const UserStats = () => {
  const [{ data: userData, loading }] = useAxios({
    withCredentials: true,
    url: `${API_URL}/users_stats`,
  });

  return (
    <>
      {!loading && (
        <SimpleGrid w="100%" spacing={5} columns={2}>
          <ReactChartCard
            chartTitle={"Users by countries"}
            chartXAxis={userData?.countries.map(
              (item: ChartDataType) => item.name
            )}
            chartDatasets={[
              {
                label: "countries",
                data: userData?.countries.map(
                  (item: ChartDataType) => item.value
                ),
                backgroundColor: userData?.countries.map(
                  (_: any, index: number) => getPallete(index)
                ),
              },
            ]}
            chartType={"pie"}
          />
          <ReactChartCard
            chartTitle={"Users by positions"}
            chartXAxis={userData?.positions.map(
              (item: ChartDataType) => item.name
            )}
            chartDatasets={[
              {
                label: "positions",
                data: userData?.positions.map(
                  (item: ChartDataType) => item.value
                ),
                backgroundColor: userData?.positions.map(
                  (_: any, index: number) => getPallete(index)
                ),
              },
            ]}
            chartType={"pie"}
          />
          <ReactChartCard
            chartTitle={"Users by account status"}
            chartXAxis={userData?.status.map(
              (item: ChartDataType) => item.name
            )}
            chartDatasets={[
              {
                label: "status",
                data: userData?.status.map((item: ChartDataType) => item.value),
                backgroundColor: [greenGenA, yellowGenA, "black", redGenA],
              },
            ]}
            chartType={"pie"}
          />
          <ReactChartCard
            chartTitle={"Users Over Time"}
            chartXAxis={userData?.created.map(
              (item: ChartDataType) => new Date(item.name)
            )}
            chartDatasets={[
              {
                label: "Number of users",
                data: userData?.created.map(
                  (item: ChartDataType) => item.value
                ),
                borderColor: brand400,
                backgroundColor: brand300a,
                fill: true,
              },
            ]}
            chartType={"line"}
            chartOptions={{
              scales: {
                x: {
                  type: "time",
                  time: {
                    unit: "week",
                    displayFormats: {
                      day: "d MMM",
                    },
                  },
                },
              },
            }}
          />
          <ReactChartCard
            chartTitle={"Search frequency"}
            chartXAxis={userData?.search_frequency.map(
              (item: ChartDataType) => new Date(item.name)
            )}
            chartDatasets={[
              {
                label: "Search result",
                data: userData?.search_frequency.map(
                  (item: ChartDataType) => item.value
                ),
                borderColor: brand400,
                backgroundColor: brand300a,
                fill: true,
              },
            ]}
            chartType={"line"}
            chartOptions={{
              scales: {
                x: {
                  type: "time",
                  time: {
                    unit: "week",
                    displayFormats: {
                      day: "d MMM",
                    },
                  },
                },
              },
            }}
          />
          <ReactChartCard
            chartTitle={"Top topics searched"}
            chartXAxis={["topics"]}
            chartDatasets={userData?.top_topics.map(
              (item: ChartDataType, index: number) => {
                return {
                  label: item.name,
                  data: [item.value],
                  backgroundColor: getPallete(index),
                };
              }
            )}
            chartOptions={{
              scales: {
                x: {
                  ticks: {
                    display: false,
                  },
                },
              },
            }}
            chartType={"bar"}
          />
        </SimpleGrid>
      )}
    </>
  );
};

export default UserStats;
