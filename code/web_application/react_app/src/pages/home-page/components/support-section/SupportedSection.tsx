import { Box, Container, Stack, Text } from "@chakra-ui/react";
import NIHLogo from "./NIHLogo";

const SupportedSection = () => {
  return (
    <Container m={0} p={0} maxW={"5xl"} opacity={"50%"}>
      <Stack
        textAlign={{ base: "center", md: "left" }}
        align={{ base: "center", md: "flex-start" }}
        spacing={4}
      >
        <Text
          textTransform={"uppercase"}
          fontSize={"sm"}
          color={"gray.500"}
          fontWeight={"700"}
          maxW={"3xl"}
        >
          A part of the The BRAIN Initiative
        </Text>
        <Box w={"100%"} maxW={{ base: "xs", sm: "xs" }}>
          <NIHLogo color={"#718096"} />
        </Box>
      </Stack>
    </Container>
  );
};

export default SupportedSection;
