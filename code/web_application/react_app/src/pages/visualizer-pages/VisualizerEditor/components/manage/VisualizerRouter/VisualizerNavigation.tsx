import { Box, Divider, Heading, HStack, Link } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import LogoWithText from "../../../../../../common/components/LogoWithText";
import useCurrentVisualizer from "../../../../hooks/useCurrentVisualizer";
import VisualizerSettings from "./VisualizerSettings";
import { Tooltip } from "@chakra-ui/react";
import { findVisualizerInfo } from "../../../../utils";

const VisualizerNavigation = () => {
  const { curVisualizer } = useCurrentVisualizer();
  const visualizerInfo = findVisualizerInfo(curVisualizer.representation);

  return (
    <Box as="nav" h="5%" zIndex={100}>
      <HStack
        align="center"
        h="100%"
        py={2}
        px={3}
        w="100%"
        bg="white"
        justify="space-between"
      >
        <HStack>
          <Tooltip hasArrow label="Back to visualizer selections" color="white">
            <Link as={RouterLink} to="/visualizers">
              <LogoWithText />
            </Link>
          </Tooltip>
          <Tooltip hasArrow label="Current visualizer" color="white">
            <Heading size="xs" px={3} fontWeight={400} color="gray.600">
              {visualizerInfo?.title}
            </Heading>
          </Tooltip>
        </HStack>
        <VisualizerSettings />
      </HStack>
      <Divider />
    </Box>
  );
};

export default VisualizerNavigation;
