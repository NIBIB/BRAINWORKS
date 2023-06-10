import { Box, Container } from "@chakra-ui/react";
import ReactChartCard from "common/components/Charts/ReactChartCard";
import PageHeader from "common/components/PageHeader";
import useAxiosWrapper from "common/hooks/useAxiosWrapper";
import { ChartDataType } from "pages/dashboard/admin/components/stats/user-stats/UserStats";
import { getPallete } from "setup/theme/utils";

const Admin = () => {
  const { getAxios: getUserStats } = useAxiosWrapper({
    url: "user_stats",
    method: "GET",
  });

  return (
    <Box py={100}>
      <PageHeader
        subTitle={"Manage"}
        title={"Administrator"}
        desc={"Manage users or view site statistics"}
        stackProps={{ pb: 50 }}
      />
      <Container maxW="6xl">
        {/* <ReactChartCard
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
        /> */}
      </Container>
    </Box>
  );
};

export default Admin;
