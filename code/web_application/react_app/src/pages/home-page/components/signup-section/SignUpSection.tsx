import { Container, Flex, Heading } from "@chakra-ui/react";
import { brand50 } from "../../../../setup/theme/colors";
import GetStartedButton from "../blocks/get-started-button/GetStartedButton";

const SignUpSection = () => {
  return (
    <Container maxW={{ base: "100%", lg: "5xl" }}>
      <Flex
        bg={brand50}
        py={{ base: 5, md: 10 }}
        px={{ base: 5, md: 10 }}
        mb={"20"}
        borderRadius={30}
        justify={{ base: "center", sm: "space-between" }}
        align={{ base: "center", sm: "" }}
        direction={{ base: "column", md: "row" }}
        gap={5}
      >
        <Heading
          fontWeight={600}
          fontSize={{ base: "xl", sm: "5xl" }}
          textAlign={{ base: "center" }}
        >
          Start creating today.
        </Heading>
        <GetStartedButton text={"Create an account"} />
      </Flex>
    </Container>
  );
};

export default SignUpSection;
