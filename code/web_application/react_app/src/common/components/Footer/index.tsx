import {
  Box,
  Container,
  HStack,
  Link,
  Stack,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import LogoWithText from "../LogoWithText";
import { FaGithub } from "react-icons/fa";
import { brand50 } from "../../../setup/theme/colors";

const Footer = () => {
  return (
    <Box
      bg={useColorModeValue(brand50, "gray.900")}
      color={useColorModeValue("gray.700", "gray.200")}
    >
      <Container as={Stack} maxW={"6xl"} py={5} fontSize={"sm"}>
        <Stack
          direction={{ base: "column", md: "row" }}
          justify={{ sm: "center", md: "space-between" }}
          align={"center"}
        >
          <Stack
            justify={{ base: "center", md: "" }}
            align={{ base: "center", md: "flex-start" }}
            spacing={0}
            mb={{ base: "5", md: "0" }}
          >
            <LogoWithText />
            <Text pl={2} fontSize={"sm"}>
              © BRAINWORKS. All rights reserved
            </Text>
          </Stack>
          <Stack
            direction={{ base: "column", md: "row" }}
            spacing={{ base: 5, md: 10 }}
            align={{ base: "center", md: "flex-start" }}
          >
            <Link
              href={"https://datascience.nih.gov/data-scholars-2022"}
              isExternal
            >
              Data Scholars
            </Link>
            <Link href={"https://braininitiative.nih.gov/"} isExternal>
              The BRAIN Intiative
            </Link>
            <HStack>
              <Link
                href={"https://github.com/deskool/brainworks-public"}
                isExternal
              >
                GitHub
              </Link>
              <FaGithub />
            </HStack>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
};

export default Footer;
