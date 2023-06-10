import { Heading, HStack } from "@chakra-ui/react";
import Logo from "../Logo";

const LogoWithText = () => {
  return (
    <HStack>
      <Logo />
      <Heading position={"relative"} as={"span"} fontWeight={"800"} size={"sm"}>
        BRAINWORKS
      </Heading>
    </HStack>
  );
};

export default LogoWithText;
