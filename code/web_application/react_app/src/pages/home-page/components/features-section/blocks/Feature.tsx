import { Box, Heading, Stack, Text, VStack } from "@chakra-ui/react";

import { brand50 } from "../../../../../setup/theme/colors";
import SubFeatures from "./SubFeatures";

export interface FeatureItemType {
  text: string;
  icon:
    | React.ReactElement<any, string | React.JSXElementConstructor<any>>
    | undefined;
  link?: string;
}

interface AppProps {
  line1: string;
  line2: string;
  desc: string;
  features: FeatureItemType[];
  visual?: React.ReactNode;
  setSubFeatureState?: React.Dispatch<React.SetStateAction<number>>;
  subFeatureState?: number;
  setStop?: React.Dispatch<React.SetStateAction<boolean>>;
}

const Feature = ({
  line1,
  line2,
  desc,
  features,
  visual,
  setSubFeatureState,
  subFeatureState,
  setStop,
}: AppProps) => {
  return (
    <Stack
      direction={{ base: "column", md: "row" }}
      bg={brand50}
      w={{ base: "95%", lg: "5xl" }}
      p={{ base: 10, sm: 50 }}
      borderRadius={"30px"}
      justify={"space-between"}
      align={"center"}
      spacing={20}
      boxShadow="lg"
    >
      <VStack
        w={{ base: "100%", md: "40%" }}
        spacing={10}
        textAlign="left"
        align="flex-start"
      >
        <Box>
          <Heading
            textAlign={{ base: "center", md: "left" }}
            fontWeight={600}
            fontSize={{ base: "3xl", sm: "5xl" }}
            lineHeight={"110%"}
          >
            {line1} {line2}
          </Heading>
          <Heading
            textAlign={{ base: "center", md: "left" }}
            fontWeight={600}
            fontSize={{ base: "3xl", md: "5xl" }}
            lineHeight={"110%"}
            mb={3}
          ></Heading>
          <Text
            textAlign={{ base: "center", md: "left" }}
            color={"gray.500"}
            fontSize={{ base: "md", md: "xl" }}
          >
            {desc}
          </Text>
        </Box>
        <SubFeatures
          features={features}
          setSubFeatureState={setSubFeatureState}
          subFeatureState={subFeatureState}
          setStop={setStop}
        />
      </VStack>

      <VStack w={{ base: "300px", sm: "420px", md: "400px", lg: "500px" }}>
        {visual}
      </VStack>
    </Stack>
  );
};

export default Feature;
