import {
  Box,
  Heading,
  Icon,
  Link,
  ListItem,
  UnorderedList,
  VStack,
} from "@chakra-ui/react";
import SkeletonImage from "common/components/SkeletonImage";
import { FiSquare } from "react-icons/fi";
import { brand400 } from "../../../../../setup/theme/colors";

const TopicCoOccurrencesInfoModal = () => {
  return (
    <VStack>
      <Box>
        <SkeletonImage
          src={
            process.env.PUBLIC_URL + "/images/topic-co-occurrences-diagram.svg"
          }
        />
      </Box>
      {/* Node information */}
      <VStack w="100%" spacing={3} align="flex-start">
        <Heading size="md">Nodes</Heading>
        <UnorderedList>
          <ListItem>
            Each node represents a{" "}
            <Link
              isExternal
              color={brand400}
              href="https://www.nlm.nih.gov/mesh/concept_structure.html"
            >
              medical subject heading (meSH)
            </Link>
          </ListItem>
          <ListItem>
            Node size corresponds to the total number of times that topic
            occurred in the literature.
          </ListItem>
        </UnorderedList>
        {/* Edges information */}
        <Heading size="md">Edges</Heading>
        <UnorderedList>
          <ListItem>
            Each edge means that the connected topics both appeared in the same
            published paper.
          </ListItem>
          <ListItem>
            Edge thickness corresponds to how frequently this co-occurrence was
            found, proportional to other edges.
          </ListItem>
          <ListItem>
            Edges are colored by whether this co-occurrence{" "}
            <Icon as={FiSquare} color="blue.500" mx={1} /> increased or{" "}
            <Icon as={FiSquare} color="red.500" mx={1} /> decreased within the
            last month.
          </ListItem>
        </UnorderedList>
        {/* Use cases */}
        <Heading size="md">Use cases</Heading>
        <UnorderedList>
          <ListItem>
            This is useful for analyzing current research trends and popular
            subjects of study.
          </ListItem>
        </UnorderedList>
      </VStack>
    </VStack>
  );
};

export default TopicCoOccurrencesInfoModal;
