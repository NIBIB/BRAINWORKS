import { Box, Card, CardBody, CardHeader, Heading } from "@chakra-ui/react";
import { ReactChartType } from "../../models";
import ReactChart from "./ReactChart";

interface AppProps {
  chartTitle: string;
}

/**
 * React Chart Card
 *
 * Wraps ReactChart with a card and adds a title to the chart
 */
const ReactChartCard = ({
  chartTitle,
  chartXAxis,
  chartDatasets,
  chartOptions,
  chartType,
}: ReactChartType & AppProps) => {
  const reactChartOptions = {
    // plugins: {
    //   legend: {
    //     position: "top" as const,
    //   },
    // },
    ...chartOptions,
  };

  return (
    <Card bg="white">
      <CardHeader>
        <Heading fontSize="md" w="100%">
          {chartTitle}
        </Heading>
      </CardHeader>
      <CardBody h={300}>
        <Box h={300} w={"100%"}>
          <ReactChart
            chartXAxis={chartXAxis}
            chartDatasets={chartDatasets}
            chartOptions={reactChartOptions}
            chartType={chartType}
          />
        </Box>
      </CardBody>
    </Card>
  );
};

export default ReactChartCard;
