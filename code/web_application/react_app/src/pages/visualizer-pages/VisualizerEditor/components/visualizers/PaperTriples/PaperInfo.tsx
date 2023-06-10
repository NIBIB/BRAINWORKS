import {
  Box,
  Button,
  Divider,
  Heading,
  HStack,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useMemo, useState } from "react";

import useCurrentVisualizer from "../../../../hooks/useCurrentVisualizer";

const MAX_AUTHORS_SHOWN = 3;

const PaperInfo = () => {
  const [expand, setExpand] = useState(false);
  const { curVisualizer } = useCurrentVisualizer();

  const { doi, pub_title, pub_date, pmid, authors, projects } = curVisualizer.data.paper;

  const handleAuthorToggle = () => {
    setExpand((prevState) => {
      return !prevState;
    });
  };

  // * Show minimum amount of authors before expansion
  const minAuthors = useMemo(() => {
    const authorArr = authors.split(",");
    let shownAuthors = authors;
    if (authorArr.length > MAX_AUTHORS_SHOWN) {
      shownAuthors = authorArr
        .slice(0, MAX_AUTHORS_SHOWN)
        .join(", ")
        .concat("...");
    }
    return shownAuthors;
  }, [authors]);

  return (
    <VStack w="100%" align="flex-start" spacing={5}>
      <Link
        color={"blue.500"}
        href={doi}
        isExternal
        w="100%"
        textAlign="center"
      >
        <Heading size={"sm"}>{pub_title}</Heading>
      </Link>
      <HStack>
        <Heading fontSize={"sm"}>Published</Heading>
        <Text> {pub_date}</Text>
      </HStack>
      {/* PMID */}
      <HStack>
        <Heading fontSize={"sm"}>PMID</Heading>
        <Text> {pmid}</Text>
      </HStack>
      {/* Projects */}
        {projects &&
        <HStack>
            <Heading fontSize={"sm"}>Projects</Heading>
            <Text> {projects}</Text>
        </HStack>
        }
      {/* Authors */}
      <VStack align="flex-start">
        <HStack>
          <Heading fontSize={"sm"}>Authors</Heading>{" "}
          <Button size="xs" variant="outline" onClick={handleAuthorToggle}>
            {expand ? "Show less" : "Show more"}
          </Button>
        </HStack>
        <Box borderColor={"gray.500"} textAlign={"left"}>
          <Text>{expand ? authors : minAuthors}</Text>
        </Box>
      </VStack>
      <Divider />
    </VStack>
  );
};

export default PaperInfo;
