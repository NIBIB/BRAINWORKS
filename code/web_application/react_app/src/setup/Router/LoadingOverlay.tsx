import { Flex, FlexProps, Spinner } from "@chakra-ui/react";

interface AppProps {
  flexProps?: FlexProps;
}

const LoadingOverlay = ({ flexProps }: AppProps) => {
  return (
    <Flex
      justify="center"
      align="center"
      position="absolute"
      w="100vw"
      h="100vh"
      {...flexProps}
    >
      <Spinner color={"brand"} size="xl" />
    </Flex>
  );
};

export default LoadingOverlay;
