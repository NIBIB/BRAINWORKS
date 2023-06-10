import { SearchIcon } from "@chakra-ui/icons";
import {
  HStack,
  Tag,
  TagCloseButton,
  TagLabel,
  Text,
  VStack,
  Wrap,
} from "@chakra-ui/react";
import { brandColorScheme } from "../../../../../setup/theme/colors";
import AnimatedText from "./AnimatedText";

const WORDS = ["Brain", "Heart", "COVID19"];

const SearchImage = () => {
  return (
    <VStack justify="flex-start" w="100%">
      <Wrap w={"100%"}>
        {WORDS.map((item) => (
          <Tag key={item} colorScheme={brandColorScheme}>
            <TagLabel>{item}</TagLabel>
            <TagCloseButton />
          </Tag>
        ))}
      </Wrap>
      <HStack
        border={"1px"}
        borderColor={"gray.300"}
        w="100%"
        py={3}
        px={2}
        align={"center"}
        justify="flex-start"
        rounded={"md"}
        boxShadow={"md"}
      >
        <SearchIcon color="gray.300" />
        <Text as={"span"}>
          <AnimatedText />
        </Text>
      </HStack>
    </VStack>
  );
};

export default SearchImage;
