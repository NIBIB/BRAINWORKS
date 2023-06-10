import { Box, Center, Container, SimpleGrid, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";

import VisualizerSelectCard from "./components/VisualizerSelectCard";
import { VISUALIZER_SELECTION } from "../templates";
import PageHeader from "../../../common/components/PageHeader";
import usePageTitle from "../../../common/hooks/usePageTitle";
import {
  fadeInChildrenItem,
  fadeInChildrenWrapper,
} from "common/templates/framer";
import AlphaTestingWarning from "common/components/AlphaTestingWarning";

/**
 * VisualizerSelect
 *
 * React component that renders the visualizer select screen. All visualizer selection cards are mapped from `VISUALIZER_SELECTION` object from the `templates` file.
 */
const VisualizerSelect = () => {
  usePageTitle("Select visualizer");

  return (
    <Container maxW="4xl" my={100}>
      <PageHeader
        subTitle="Selection"
        title="Choose your visualizer"
        desc="Analyze scientific literature to transform knowledge, and reveal emerging patterns."
        stackProps={{ mb: 50 }}
      />
      <Center>
        <VStack maxW="6xl" w="100%" align="center">
          <Box mb={50}>
            <AlphaTestingWarning />
          </Box>
          <SimpleGrid
            as={motion.div}
            columns={{ base: 1, md: 2 }}
            spacingY={{ base: "15px", sm: "20px" }}
            spacingX={{ base: "15px", sm: "20px" }}
            variants={fadeInChildrenWrapper}
            initial="hidden"
            animate="show"
          >
            {VISUALIZER_SELECTION.map((tool) => (
              <motion.div variants={fadeInChildrenItem} key={tool.route}>
                <VisualizerSelectCard
                  title={tool.title}
                  desc={tool.desc}
                  img={tool.img}
                  route={tool.route}
                />
              </motion.div>
            ))}
          </SimpleGrid>
        </VStack>
      </Center>
    </Container>
  );
};

export default VisualizerSelect;
