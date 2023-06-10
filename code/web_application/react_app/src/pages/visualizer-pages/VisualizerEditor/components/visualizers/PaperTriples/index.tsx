import {
  Box,
  Container,
  Heading,
  Highlight,
  HStack,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from "@chakra-ui/react";
import { useMemo, useState } from "react";

import useCurrentVisualizer from "../../../../hooks/useCurrentVisualizer";
import TableFragment from "./TableFragment";
import { brand100 } from "../../../../../../setup/theme/colors";
import { createTriplesTable } from "../../../../utils";
import PaperInfo from "./PaperInfo";

const PaperTriples = () => {
  const { curVisualizer } = useCurrentVisualizer();
  const [highlight, setHighlight] = useState(-1);

  const { triples, paper } = curVisualizer.data;

  const triplesTableData = useMemo(() => {
    return createTriplesTable(triples);
  }, [triples]);

  return (
    <HStack align="center" h="95%" justify="space-around">
      {/* Triples Table */}
      <VStack w="40%" align="flex-start" spacing={5}>
        <TableContainer
          bg="white"
          maxH="90vh"
          boxShadow="lg"
          overflowY="auto"
          p={5}
          borderRadius="lg"
        >
          <Table variant="simple" size="xs" fontSize="xs">
            <Thead>
              <Tr>
                <Th>Subject</Th>
                <Th mr={3}>Relation</Th>
                <Th>Object</Th>
              </Tr>
            </Thead>
            <Tbody>
              {/* Triple sentence */}
              {triplesTableData.map((triple: any, tripleNum: number) => (
                <Tr
                  bg={highlight === tripleNum ? "gray.300" : ""}
                  key={`triple${tripleNum}`}
                  onClick={() => {
                    document
                      .querySelector(triple.target)
                      .scrollIntoView({ behavior: "smooth" });
                  }}
                  onMouseEnter={() => {
                    setHighlight(tripleNum);
                  }}
                  onMouseLeave={() => {
                    setHighlight(-1);
                  }}
                >
                  {/* Object fragments */}
                  <Td>
                    {triple.subFrags.map((obj: any) => (
                      <TableFragment text={obj?.text} def={obj?.def} />
                    ))}
                  </Td>
                  <Td>{triple.relation}</Td>
                  <Td>
                    {triple.objFrags.map((obj: any) => (
                      <TableFragment text={obj?.text} def={obj?.def} />
                    ))}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </TableContainer>
      </VStack>
      {/* Abstract */}
      <Container
        maxW="3xl"
        fontSize="xs"
        bg="white"
        h="90vh"
        boxShadow="lg"
        overflowY="auto"
        p={10}
      >
        <VStack align="flex-start" spacing={5}>
          <PaperInfo />
          <Heading size="md">Abstract</Heading>
          <Box>
            {paper.abstract.map((sentence: any) => {
              const text = sentence[0];
              // * If section has 2nd item, an associated triples exist
              if (sentence[1] !== undefined) {
                const tripleNum = sentence[1];
                return (
                  <Box
                    bg={highlight === tripleNum ? "gray.300" : ""}
                    as="span"
                    data-index={tripleNum}
                    onMouseEnter={() => {
                      setHighlight(tripleNum);
                    }}
                    onMouseLeave={() => {
                      setHighlight(-1);
                    }}
                    key={`triple${tripleNum}`}
                  >
                    <Highlight
                      query={[
                        triples[tripleNum].object,
                        triples[tripleNum].relation,
                        triples[tripleNum].subject,
                      ]}
                      styles={{ bg: brand100 }}
                    >
                      {text}
                    </Highlight>
                  </Box>
                );
              }
              return <Text display="inline">{text}</Text>;
            })}
          </Box>
        </VStack>
      </Container>
    </HStack>
  );
};

export default PaperTriples;
