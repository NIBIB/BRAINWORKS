import {
  Box,
  Heading,
  Highlight,
  Link,
  ListItem,
  Table,
  TableContainer,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  UnorderedList,
  VStack,
} from "@chakra-ui/react";
import { brand400 } from "../../../../../setup/theme/colors";

/**
 * PaperTriplesInfoModal
 *
 * React component that renders an short information explanation of the paper triples tool
 */
const PaperTriplesInfoModal = () => {
  return (
    <VStack>
      {/* Triple information */}
      <VStack w="100%" spacing={3} align="flex-start">
        {/* Explanation of a triple */}
        <Heading size="md">Semantic triples</Heading>
        <TableContainer bg="gray.50">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Subject</Th>
                <Th>Relation</Th>
                <Th>Object</Th>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td>term</Td>
                <Td>relationship</Td>
                <Td>term</Td>
              </Tr>
            </Tbody>
          </Table>
        </TableContainer>
        <UnorderedList>
          <ListItem>
            A semantic triple is a sentence distilled into 3 parts: subject,
            relation, and object.
          </ListItem>
          <ListItem>
            The triple's structure is based on the{" "}
            <Link
              isExternal
              color={brand400}
              href="https://www.nlm.nih.gov/research/umls/index.html"
            >
              Unified Medical Language System (ULMS)
            </Link>
            .
          </ListItem>
        </UnorderedList>
        {/* Example */}
        <Heading size="md">Example</Heading>
        <Box fontStyle="italic">
          <Highlight
            query={["fox", "dog", "jumps"]}
            styles={{
              bg: "blue.100",
            }}
          >
            "The quick brown fox jumps over the lazy dog"
          </Highlight>
        </Box>
        <TableContainer bg="gray.50">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Subject</Th>
                <Th>Relation</Th>
                <Th>Object</Th>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td>fox</Td>
                <Td>jumps</Td>
                <Td>dog</Td>
              </Tr>
            </Tbody>
          </Table>
        </TableContainer>
        {/* Use cases */}
        <Heading size="md">Use cases</Heading>
        <UnorderedList>
          <ListItem>
            This is useful for revealing all findings from a single paper
          </ListItem>
        </UnorderedList>
      </VStack>
    </VStack>
  );
};

export default PaperTriplesInfoModal;
