import { useColorModeValue } from "@chakra-ui/react";

const useBorderColor = () => {
  const borderColor = useColorModeValue("gray.300", "gray.300");
  return borderColor;
};

export default useBorderColor;
