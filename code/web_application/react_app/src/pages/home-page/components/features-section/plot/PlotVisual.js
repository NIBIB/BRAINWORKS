import { Box, Text, VStack } from "@chakra-ui/react";
import { useEffect } from "react";
import GetStartedButton from "../../blocks/get-started-button/GetStartedButton";
import {
  EXAMPLE_PAPER_CITATIONS,
  EXAMPLE_TOPIC_CO_OCCURENCES,
  EXAMPLE_TRIPLES,
} from "./templates/static-plots";
import { motion } from "framer-motion";

const GraphAPI = ({ id }) => {
  return (
    <Box
      boxShadow={"md"}
      border={"1px"}
      borderColor={"gray.300"}
      bg={"black"}
      w={"100%"}
      id={id}
      h={"100%"}
      pos={"relative"}
    ></Box>
  );
};

const PlotTemplate = ({ id, stop }) => {
  return (
    <>
      {stop ? (
        <motion.div
          style={{ width: "100%", height: "100%" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, ease: "easeInOut" }}
        >
          <GraphAPI id={id} />
        </motion.div>
      ) : (
        <motion.div
          style={{ width: "100%", height: "100%" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 2, ease: "easeInOut" }}
        >
          <GraphAPI id={id} />
        </motion.div>
      )}
    </>
  );
};

const PaperCitationPlot = ({ stop }) => {
  useEffect(() => {
    try {
      window.ex_paper_citations = new window.Graph(EXAMPLE_PAPER_CITATIONS, {
        container: "ex_paper_citations",
        gravity: 1,
        toolbar: [],
        physics: true,
      });
    } catch {}
  }, []);
  return <PlotTemplate stop={stop} id={"ex_paper_citations"} />;
};

const TopicCoOccurencesPlot = ({ stop }) => {
  useEffect(() => {
    try {
      window.ex_topic_co_occurences = new window.Graph(
        EXAMPLE_TOPIC_CO_OCCURENCES,
        {
          container: "ex_topic_co_occurences",
          gravity: 1,
          toolbar: [],
          physics: true,
        }
      );
    } catch {}
  }, []);
  return <PlotTemplate stop={stop} id={"ex_topic_co_occurences"} />;
};

const TriplesPlot = ({ stop }) => {
  useEffect(() => {
    try {
      window.ex_triples = new window.Graph(EXAMPLE_TRIPLES, {
        container: "ex_triples",
        gravity: 1,
        toolbar: [],
        physics: true,
      });
    } catch {}
  }, []);
  return <PlotTemplate stop={stop} id={"ex_triples"} />;
};

const Plots = ({ carousel, stop }) => {
  const plotProps = {
    stop: stop,
  };

  if (carousel === 0) {
    return <TriplesPlot {...plotProps} />;
  }
  if (carousel === 1) {
    return <PaperCitationPlot {...plotProps} />;
  }
  return <TopicCoOccurencesPlot {...plotProps} />;
};

const PlotVisual = ({ carousel, setStop, stop }) => {
  return (
    <VStack w={"100%"} h={"420px"} spacing={3}>
      <Plots carousel={carousel} stop={stop} />
      <Text fontSize={"12px"} color={"gray.500"}>
        Interact with our plot tool using a sample data set.
      </Text>
      <GetStartedButton text={"Have a topic in mind?"} />
    </VStack>
  );
};

export default PlotVisual;
