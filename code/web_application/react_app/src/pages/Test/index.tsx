import {
  Box,
  Button,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Heading,
  Input,
  InputGroup,
  InputLeftAddon,
} from "@chakra-ui/react";
import ReactChart from "common/components/Charts/ReactChart";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
import { Field } from "formik";
import { ChartDataType } from "pages/dashboard/admin/components/stats/user-stats/UserStats";
import { useEffect, useMemo, useState } from "react";
import { brand300a, brand400 } from "setup/theme/colors";
import { getPallete } from "setup/theme/utils";

const Test = () => {
  const { getAxios } = useAxiosWrapper({
    url: "test",
    method: "GET",
  });
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [arr, setArr] = useState([]);
  useEffect(() => {
    const getData = async () => {
      setLoading(true);
      const { data: charts } = await getAxios();
      setData(charts.success);
      console.log(charts);
      const newData = charts.success.map((dataSet: any, index: number) => {
        return {
          label: `${dataSet.topic} citations`,
          data: dataSet.data.map((item: ChartDataType) => item.value),
          borderColor: getPallete(index),
          backgroundColor: getPallete(index),
          tension: 0.1,
        };
      });
      setArr(newData);
      setLoading(false);
    };
    getData();
  }, []);

  return (
    <>
      {loading ? (
        <div>loading </div>
      ) : (
        <Card maxW="5xl" bg="white" h="500px">
          <CardHeader>
            <Heading size="md">Citation interest over time</Heading>
          </CardHeader>
          <CardBody>
            <ReactChart
              // Picking arbitrary dataset to be x-axis because they're the same
              chartXAxis={data[0].data.map(
                (item: ChartDataType) => new Date(item.name)
              )}
              chartDatasets={arr}
              chartType={"line"}
              chartOptions={{
                plugins: {
                  hover: {
                    mode: "index",
                    intersect: false,
                  },
                  tooltip: {
                    mode: "index",
                    intersect: false,
                    includeInvisible: true,
                  },
                },
                elements: {
                  point: {
                    radius: 0,
                  },
                },
                scales: {
                  x: {
                    grid: {
                      display: false,
                      drawBorder: false,
                    },

                    type: "time",
                    time: {
                      unit: "month",
                      displayFormats: {
                        month: "MMM",
                      },
                    },
                  },
                  y: {
                    gridLines: {
                      display: true,
                    },
                    grid: {
                      display: true,
                      drawBorder: false,
                    },
                  },
                },
              }}
            />
          </CardBody>
        </Card>
      )}{" "}
    </>
  );
};

export default Test;
