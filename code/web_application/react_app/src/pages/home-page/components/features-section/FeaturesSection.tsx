import {
  Box,
  Center,
  Container,
  Divider,
  Heading,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { chakraHighlight } from "../../../../setup/theme/utils/chakraHighlight";
import FeatureGridLayout from "../blocks/feature-text-image/FeatureGridLayout";
import FeatureImage from "../blocks/feature-text-image/FeatureImage";
import FeatureText from "../blocks/feature-text-image/FeatureText";
import GetStartedButton from "../blocks/get-started-button/GetStartedButton";
import PaperFeature from "./paper/PaperFeature";
import PlotFeature from "./plot/PlotFeature";
import SearchImage from "./search-image/SearchImage";

const Features = () => {
  return (
    <Box>
      <Container maxW={"5xl"} mt={"28"}>
        <Stack textAlign={"center"} align={"center"} spacing={5}>
          {/* Heading */}
          <Stack
            textAlign={"center"}
            align={"center"}
            spacing={{ base: 8, md: 5 }}
            m={{ base: "0", sm: "auto" }}
          >
            <Heading
              fontWeight={700}
              fontSize={{ base: "4xl", sm: "6xl" }}
              lineHeight={"110%"}
              textAlign={{ base: "left", sm: "center" }}
            >
              <Text
                as={"span"}
                color={"brand"}
                position={"relative"}
                _after={{ ...chakraHighlight }}
              >
                Explore
              </Text>{" "}
              our tools.
            </Heading>
            <GetStartedButton text={"Create your own visual"} />
          </Stack>
        </Stack>
        <FeatureGridLayout simpleGridProps={{ py: { base: "20", md: "0" } }}>
          <FeatureText
            left={true}
            head={"Start with a single keystroke."}
            desc={
              "Find what you need, whether that be a single topic or a dozen combined."
            }
          />
          <FeatureImage image={<SearchImage />} />
        </FeatureGridLayout>
        <Divider />
      </Container>

      <VStack spacing={10} my={{ base: 20, sm: 28 }}>
        <PlotFeature />
        <PaperFeature />
      </VStack>
      <Center>
        <Divider maxW={"5xl"} />
      </Center>
    </Box>
  );
};

export default Features;
