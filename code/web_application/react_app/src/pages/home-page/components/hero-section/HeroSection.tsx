import { Container, Heading, Stack, Text, Center, Box } from "@chakra-ui/react";
import { brand100, brand50 } from "../../../../setup/theme/colors";
import { chakraHighlight } from "../../../../setup/theme/utils/chakraHighlight";
import GetStartedButton from "../blocks/get-started-button/GetStartedButton";
import SupportedSection from "../support-section/SupportedSection";
import HeroDemo2 from "./animated-demo/HeroDemo";
import { Parallax } from "react-scroll-parallax";

const HeroSection = () => {
  return (
    <Center h={"100%"}>
      <Stack
        bg={brand50}
        direction={{ base: "column", lg: "row" }}
        align={{ base: "center", lg: "center" }}
        justify="space-between"
        h={{ base: "auto", lg: "100vh" }}
        maxH="100%"
        w={"100%"}
        p={{ base: 10, md: 10 }}
        pt={100}
        spacing={10}
        pos="relative"
        overflow="clip"
      >
        <Container w={"100%"} zIndex={1}>
          <Stack
            ml={0}
            pl={0}
            textAlign={{ base: "center", md: "left" }}
            align={{ base: "center", md: "flex-start" }}
            spacing={5}
          >
            <Heading
              fontWeight={700}
              fontSize={{ base: "4xl", sm: "6xl" }}
              lineHeight={"110%"}
            >
              <Text
                as={"span"}
                color={"brand"}
                position={"relative"}
                _after={{ ...chakraHighlight }}
              >
                Visualize
              </Text>{" "}
              the scientific literature.
            </Heading>
            <Text
              maxW={{ base: "auto", sm: "xl" }}
              fontSize={{ base: "md", sm: "xl" }}
              color={"gray.500"}
            >
              Transform knowledge, connect concepts, and track emerging
              patterns. Use 40 years of published scientific work combined with
              a rich set of interactive tools powered by machine learning.
            </Text>
            <GetStartedButton text={"Get started"} />
            <SupportedSection />
          </Stack>
        </Container>
        <HeroDemo2 />
        <Box display={{ base: "none", md: "block" }}>
          <Parallax
            style={{ position: "absolute", top: "-10px", right: "-120px" }}
            speed={50}
          >
            <Box
              opacity="20%"
              borderRadius={"50%"}
              h="800px"
              w="800px"
              bg={brand100}
              zIndex={0}
            />
          </Parallax>
        </Box>
        <Box display={{ base: "none", md: "block" }}>
          <Parallax
            style={{ position: "absolute", bottom: "50%", left: "-120px" }}
            speed={50}
          >
            <Box
              opacity="20%"
              borderRadius={"50%"}
              h="300px"
              w="300px"
              bg={brand100}
              zIndex={0}
            />
          </Parallax>
        </Box>
      </Stack>
    </Center>
  );
};

export default HeroSection;
