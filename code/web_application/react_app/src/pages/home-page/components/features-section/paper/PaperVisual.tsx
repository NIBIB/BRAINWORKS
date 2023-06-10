import {
  Box,
  Link,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tooltip,
  Tr,
  VStack,
  Wrap,
  WrapItem,
} from "@chakra-ui/react";
import { useState } from "react";
import GetStartedButton from "../../blocks/get-started-button/GetStartedButton";

// * Mapping segments of the article to its type: "text", "subject", "relation", "object"
const ARTICLE = [
  [
    { text: "During March-May 2021, ", type: "text" },
    { text: "SARS-CoV-2", type: "subject" },
    { text: " ", type: "text" },
    { text: "mRNA", type: "subject" },
    {
      text: " vaccines were highly effective for ",
      type: "text",
    },
    {
      text: "preventing hospitalizations among",
      type: "relation",
    },
    {
      text: " US ",
      type: "text",
    },
    { text: "adults", type: "object" },
    { text: ".", type: "text" },
  ],
  [
    { text: "SARS-CoV-2", type: "subject" },
    { text: " ", type: "text" },
    { text: "vaccination", type: "subject" },
    { text: " ", type: "text" },
    { text: "was beneficial for", type: "relation" },
    { text: " ", type: "text" },
    { text: "patients", type: "object" },
    { text: " with ", type: "text" },
    { text: "immunosuppression", type: "object" },
    {
      text: " but effectiveness was lower in the immunosuppressed population.",
      type: "text",
    },
  ],
  [
    { text: "Vaccine", type: "subject" },
    { text: " ", type: "text" },
    { text: "effectiveness", type: "subject" },
    { text: " ", type: "text" },
    { text: "was lower among", type: "relation" },
    { text: " ", type: "text" },
    { text: "patients", type: "object" },
    { text: " with ", type: "text" },
    { text: "immunosuppression", type: "object" },
    {
      text: " (62.9%; 95% CI,20.8-82.6) than without immunosuppression (91.3%; 95% CI, 85.6-94.8).",
      type: "text",
    },
  ],
];

// * Map each triple to corresponding tooltip if it has one
const TRIPLES = [
  {
    subject: [
      {
        text: "SARS-CoV-2",
        def: "Any viral organism that can be assigned to the severe acute respiratory syndrome Coronavirus 2.",
      },
      {
        text: "mRNA",
        def: "A substance or group of substances administered to induce the immune system to recognize and destroy tumors of microorganisms, which can be used for preventation, amelioration, or treatment of disease.",
      },
    ],
    relation: "preventing hospitalizations",
    object: [
      {
        text: "US",
      },
      {
        text: "Adults",
        def: "A person having attained full growth or maturity.",
      },
    ],
    color: "blue",
  },
  {
    subject: [
      {
        text: "SARS-CoV-2",
        def: "Any viral organism that can be assigned to the severe acute respiratory syndrome Coronavirus 2.",
      },
      {
        text: "vaccination",
        def: "Administration of vaccines to stimulate the host's immune response. This includes any preparation intended for active immunological prophylaxis or treatment.",
      },
    ],
    relation: "was beneficial for",
    object: [
      {
        text: "patients",
        def: "A patient is the subject of observations.",
      },
      {
        text: "with",
      },
      {
        text: "immunosuppression",
        def: "Therapy used to decrease the body's immune response, such as drugs given to prevent transplant rejection.",
      },
    ],
    color: "red",
  },
  {
    subject: [
      {
        text: "Vaccine",
        def: "A substance or group of substances administered to induce the immune system to recognize and destroy tumors or microorganisms, which can be used for prevention, amelioration, or treatment of diseases.",
      },
      {
        text: "effectiveness",
        def: "In medicine, the ability of an intervention (for example, a drug or surgery) to produce the desired beneficial effect.",
      },
    ],
    relation: "was lower among",
    object: [
      {
        text: "patients",
        def: "A patient is the subject of observations.",
      },
      {
        text: "with",
      },
      {
        text: "immunosuppression",
        def: "Therapy used to decrease the body's immune response, such as drugs given to prevent transplant rejection.",
      },
    ],
    color: "green",
  },
];

// * Diciontary to determine background color gradient
const BGCOLOR: { [key: string]: number } = {
  subject: 200,
  relation: 1000,
  object: 200,
  text: 1000, // This color doesn't exist, so black is defaulted
};

const PaperVisual = () => {
  const [hover, setHover] = useState(-1);

  return (
    <VStack w={"100%"} spacing={3}>
      <Box
        border={"1px"}
        borderColor={"gray.300"}
        bg={"white"}
        fontSize={"xs"}
        boxShadow={"md"}
        p={10}
      >
        {ARTICLE.map((sentence, index) => {
          return (
            <>
              <Text
                background={hover === index ? "gray.300" : ""}
                onMouseOver={() => {
                  setHover(index);
                }}
                onMouseLeave={() => {
                  setHover(-1);
                }}
                as={"span"}
              >
                {sentence.map((item) => {
                  return (
                    <Box
                      as={"span"}
                      bg={
                        hover === index
                          ? `${TRIPLES[index].color}.${BGCOLOR[item.type]}`
                          : ""
                      }
                    >
                      {item.text}
                    </Box>
                  );
                })}
              </Text>{" "}
            </>
          );
        })}
      </Box>
      <TableContainer
        bg="white"
        bottom={0}
        border={"1px"}
        borderColor={"gray.300"}
        boxShadow={"md"}
      >
        <Table
          size={"sm"}
          fontSize={"10px"}
          id="triples_table"
          variant="striped"
          colorScheme="blackAlpha"
          whiteSpace="normal"
        >
          <Thead>
            <Tr>
              <Th px={2}>Subject</Th>
              <Th>Relation</Th>
              <Th>Object</Th>
            </Tr>
          </Thead>
          <Tbody>
            {TRIPLES.map((item, i) => (
              <Tr
                onMouseOver={() => {
                  setHover(i);
                }}
                onMouseLeave={() => {
                  setHover(-1);
                }}
                key={i}
              >
                <Td px={2}>
                  <Wrap>
                    {item.subject.map((item) => (
                      <WrapItem>
                        <Tooltip label={item.def} color="white">
                          <Text
                            fontSize={"12px"}
                            maxW="auto"
                            bg={hover === i ? `${TRIPLES[i].color}.200` : ""}
                          >
                            {item.text}
                          </Text>
                        </Tooltip>
                      </WrapItem>
                    ))}
                  </Wrap>
                </Td>
                <Td>
                  <Wrap>
                    <WrapItem>
                      <Text fontSize={"12px"}>{item.relation}</Text>
                    </WrapItem>
                  </Wrap>
                </Td>
                <Td>
                  <Wrap>
                    {item.object.map((item) => {
                      if (item.def) {
                        return (
                          <WrapItem key={`def_${item}`}>
                            <Tooltip label={item.def} color="white">
                              <Text
                                fontSize={"12px"}
                                bg={
                                  hover === i ? `${TRIPLES[i].color}.200` : ""
                                }
                              >
                                {item.text}
                              </Text>
                            </Tooltip>
                          </WrapItem>
                        );
                      } else {
                        return <Text fontSize={"12px"}> {item.text}</Text>;
                      }
                    })}
                  </Wrap>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
      <Link
        isExternal
        color={"gray.500"}
        href={"https://academic.oup.com/cid/article/74/9/1515/6343399"}
      >
        <Text fontSize={"12px"}>
          Interact with an actual exerpt and table generated by our tool
        </Text>
      </Link>
      <GetStartedButton text={"Have a paper in mind?"} />
    </VStack>
  );
};

export default PaperVisual;
