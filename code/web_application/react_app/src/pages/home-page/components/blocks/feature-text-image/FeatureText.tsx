import {
  Heading,
  HStack,
  Icon,
  Link,
  StackProps,
  Text,
  TextProps,
  VStack,
} from "@chakra-ui/react";
import { FiArrowRight } from "react-icons/fi";

interface AppProps {
  head: string;
  desc: string;
  left: boolean;
  vStackProps?: StackProps;
  link?: string;
  linkPrompt?: string;
}

/**
 * @param left - boolean to determine if the text will align left or right
 * @param head - text for the header of the step
 * @param desc - text for step description
 * @param vStackProps - ChakraUI props for VStack component
 * @param link - optionally add a link at the very end
 * @param linkPrompt - optionally add some text to the link
 * @returns the text for the step section
 */
const FeatureText = ({
  left,
  head,
  desc,
  vStackProps,
  link,
  linkPrompt,
}: AppProps) => {
  const textStyleProps: TextProps = {
    textAlign: { base: "center", md: "left" },
    fontSize: { base: "md", sm: "xl" },
  };

  return (
    <VStack
      align={{ base: "center", md: "flex-start" }}
      justify={"center"}
      spacing={4}
      maxW={"sm"}
      mx={{ base: "0", sm: "auto" }}
      {...vStackProps}
    >
      <Heading
        fontWeight={600}
        fontSize={{ base: "xl", sm: "5xl" }}
        lineHeight="110%"
        textAlign={{ base: "center", md: "left" }}
      >
        {head}
      </Heading>
      <Text color="gray.500" {...textStyleProps}>
        {desc}
      </Text>
      {link && (
        <Link color="blue.500" href={link} isExternal>
          <HStack>
            <Text {...textStyleProps}>{linkPrompt}</Text>
            <Icon as={FiArrowRight} w={5} h={5} />
          </HStack>
        </Link>
      )}
    </VStack>
  );
};

export default FeatureText;
