import { Box, Heading, HStack } from "@chakra-ui/react";

import ReactChart from "../../../../../../common/components/Charts/ReactChart";
import { brand300a, brand400 } from "../../../../../../setup/theme/colors";

interface AppProps {
  label: string;
  data: number[];
  years: number[];
  triples: string[];
}

const TripleTimeline = ({ triples, label, data, years }: AppProps) => {
  return (
    <HStack align="center" w="100%">
      {/* Label of item */}
      <Heading
        fontSize="xs"
        fontWeight={400}
        w={150}
        style={{ hyphens: "auto" }}
        pl={3}
      >
        {label}
      </Heading>
      {/* Frequency */}
      <Box w="100%" h={triples.length < 10 ? 200 : 50}>
        <ReactChart
          chartXAxis={years}
          chartDatasets={[
            {
              label: label,
              data: data,
              borderColor: brand400,
              backgroundColor: brand300a,
              fill: true,
              tension: 0.1,
            },
          ]}
          chartType={"line"}
          chartOptions={{
            plugins: {
              legend: {
                display: false,
              },
              tooltip: {
                caretSize: 0,
              },
            },
            scales: {
              x: {
                ticks: {
                  display: false,
                },
                grid: {
                  display: false,
                  drawBorder: false,
                },
              },
              y: {
                ticks: {
                  display: false,
                },
                gridLines: {
                  display: true,
                  drawOnChartArea: false,
                  drawTicks: false,
                },
                grid: {
                  display: false,
                  drawBorder: false,
                },
              },
            },
          }}
        />
      </Box>
    </HStack>
  );
};

export default TripleTimeline;
