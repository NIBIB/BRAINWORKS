import { Heading, StackProps, Text, VStack } from "@chakra-ui/react";
import { brand500 } from "../../../setup/theme/colors";

interface AppProps {
  subTitle: string;
  title: string;
  desc: string;
  direction?: "center" | "left" | "right";
  stackProps?: StackProps;
}

const PageHeader = ({
  subTitle,
  title,
  desc,
  direction,
  stackProps,
}: AppProps) => {
  // * Change direction of page header
  let align = "center";
  if (direction) {
    if (direction === "left") {
      align = "flex-start";
    }
    if (direction === "right") {
      align = "flex-end";
    }
  }

  return (
    <VStack
      w="100%"
      spacing={5}
      textAlign="center"
      align={align}
      {...stackProps}
    >
      <Heading size="sm" color={brand500}>
        {subTitle}
      </Heading>
      <Heading size="2xl">{title}</Heading>
      <Text fontSize="xl" color="gray.600">
        {desc}
      </Text>
    </VStack>
  );
};

export default PageHeader;
