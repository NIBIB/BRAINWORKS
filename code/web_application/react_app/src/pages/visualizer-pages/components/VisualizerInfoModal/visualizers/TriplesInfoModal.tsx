import {
  Box,
  Heading,
  Icon,
  ListItem,
  UnorderedList,
  VStack,
} from "@chakra-ui/react";
import SkeletonImage from "common/components/SkeletonImage";
import { FiSquare } from "react-icons/fi";

const TriplesInfoModal = () => {
  return (
    <VStack align="center">
      <Box>
        <SkeletonImage
          src={process.env.PUBLIC_URL + "/images/triples-diagram.svg"}
        />
      </Box>
      {/* Node information */}
      <VStack w="100%" spacing={3} align="flex-start">
        <Heading size="md">Nodes</Heading>
        <UnorderedList>
          <ListItem>Each node represents a research concept</ListItem>
          <ListItem>Nodes are colored to differentiate topic clusters</ListItem>
        </UnorderedList>
        {/* Edges information */}
        <Heading size="md">Edges</Heading>
        <UnorderedList>
          <ListItem>
            Each edge represents a finding that connects two concepts, pulled
            from a published article. Edge thickness corresponds to the number
            of citations that paper has.
          </ListItem>
          <ListItem>
            Edges are colored according to the type of relationship:{" "}
            <Icon as={FiSquare} color="blue.500" mx={1} /> Positive{" "}
            <Icon as={FiSquare} color="red.500" mx={1} /> Negative.
          </ListItem>
          <ListItem>
            Each edge means that the connected topics both appeared in the same
            published paper.
          </ListItem>
        </UnorderedList>
        {/* Use cases */}
        <Heading size="md">Use cases</Heading>
        <UnorderedList>
          <ListItem>
            This is useful for finding commonalities between multiple papers.
          </ListItem>
        </UnorderedList>
      </VStack>
    </VStack>
  );
};

export default TriplesInfoModal;
