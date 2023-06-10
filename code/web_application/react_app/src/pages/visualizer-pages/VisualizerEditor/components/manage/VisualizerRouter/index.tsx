import { ReactNode, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import useGlobalAlert from "../../../../../../common/hooks/useGlobalAlert";
import GraphAPI from "../../visualizers/GraphAPI";
import usePageTitle from "../../../../../../common/hooks/usePageTitle";
import VisualizerNavigation from "./VisualizerNavigation";
import { useAppSelector } from "../../../../../../store/hooks";
import { Box } from "@chakra-ui/react";
import PaperTriples from "../../visualizers/PaperTriples";
import FrequencyTimelines from "../../visualizers/FrequencyTimelines";

// * Dictionary determines which visualizer component should render based on type
const VISUALIZERS: { [visualizer: string]: ReactNode } = {
  triples: <GraphAPI />,
  topic_co_occurrences: <GraphAPI />,
  paper_citations: <GraphAPI />,
  paper_triples: <PaperTriples />,
  frequency_timelines: <FrequencyTimelines />,
};

/**
 * VisualizerRouter
 */
const VisualizerRouter = () => {
  const navigate = useNavigate();
  const curVisualizer = useAppSelector((state) => state.visualizer);
  const { showGlobalAlert } = useGlobalAlert();
  usePageTitle("Editor");

  useEffect(() => {
    // * If visualizer component is not found, navigate back to the home page
    if (
      curVisualizer?.representation === undefined ||
      VISUALIZERS[curVisualizer?.representation] === undefined
    ) {
      showGlobalAlert(
        "Error",
        "Your visual could not be found. Please try again.",
        "error",
        5000
      );
      navigate("/test");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curVisualizer?.representation]);

  return (
    <Box h="100vh">
      <VisualizerNavigation />
      {VISUALIZERS[curVisualizer?.representation]}
    </Box>
  );
};

export default VisualizerRouter;
