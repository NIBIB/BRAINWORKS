import { Flex } from "@chakra-ui/react";
import PageHeader from "common/components/PageHeader";
import usePageTitle from "../../common/hooks/usePageTitle";

/**
 * Error404
 *
 * React component that renders when a page is not found
 */
const Error404 = () => {
  usePageTitle("Page not found");

  return (
    <Flex h="80vh" align="center" justify="center">
      <PageHeader
        subTitle={"404"}
        title={"Page not found"}
        desc={"This page does not exist."}
      />
    </Flex>
  );
};

export default Error404;
