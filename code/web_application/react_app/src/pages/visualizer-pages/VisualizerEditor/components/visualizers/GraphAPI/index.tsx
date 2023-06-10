import $ from "jquery";
import { Box } from "@chakra-ui/react";
import { useEffect } from "react";

import useCurrentVisualizer from "../../../../hooks/useCurrentVisualizer";
import { gray50 } from "../../../../../../setup/theme/colors";
import { configure_graph } from "./graphAPIUtils";

const GraphAPI = () => {
  const { curVisualizer } = useCurrentVisualizer();

  useEffect(() => {
    configure_graph(curVisualizer.data, curVisualizer.representation);

    const timer = setTimeout(() => {
      // * Changing background color to light gray
      $("iframe")
        .contents()
        .find("#sigma-container")
        .css({ backgroundColor: gray50 });
      document.body.style.backgroundColor = gray50;
    }, 300);

    return () => {
      clearTimeout(timer);
    };
  }, [curVisualizer.data, curVisualizer.representation]);

  return <Box id="graphAPI-container" w="100vw" height="95%" zIndex={-1}></Box>;
};

export default GraphAPI;
