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

const PaperCitationsInfoModal = () => {
  return (
    <VStack>
      <Box>
        <SkeletonImage
          src={process.env.PUBLIC_URL + "/images/paper-citations-diagram.svg"}
        />
      </Box>
      {/* Node information */}
      <VStack w="100%" spacing={3} align="flex-start">
        <Heading size="md">Nodes</Heading>
        <UnorderedList>
          <ListItem>
            Each <Icon as={FiSquare} color="red.500" mx={1} /> node is a
            published paper relating to your search terms.
          </ListItem>
          <ListItem>
            Each <Icon as={FiSquare} color="yellow.500" mx={1} /> node is a
            published paper that cites any of the papers you searched for.
          </ListItem>
        </UnorderedList>
        {/* Edges information */}
        <Heading size="md">Edges</Heading>
        <UnorderedList>
          <ListItem>Each edge is simply a citation between papers.</ListItem>
        </UnorderedList>
        {/* Use cases */}
        <Heading size="md">Use cases</Heading>
        <UnorderedList>
          <ListItem>
            This is useful for tracking down the origin of findings of topics.
          </ListItem>
        </UnorderedList>
      </VStack>
    </VStack>
  );
};

export default PaperCitationsInfoModal;
