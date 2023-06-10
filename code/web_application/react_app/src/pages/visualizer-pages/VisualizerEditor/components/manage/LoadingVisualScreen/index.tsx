import { Spinner, VStack } from "@chakra-ui/react";
import usePageTitle from "../../../../../../common/hooks/usePageTitle";
import PageHeader from "../../../../../../common/components/PageHeader";

/**
 *
 * @returns
 */
const LoadingVisualScreen = () => {
  usePageTitle("Loading");

  return (
    <VStack w="100%" h="100vh" justify="Center" spacing={20}>
      <PageHeader
        subTitle={"Building"}
        title={"Loading visualizer"}
        desc={
          "Please do not leave or refresh this page while your visual is being created."
        }
      />
      <Spinner color={"brand"} size="xl" />
    </VStack>
  );
};

export default LoadingVisualScreen;
