import { Avatar, Box, BoxProps, HStack, Icon, Text } from "@chakra-ui/react";
import { FaFolder, FaGithub } from "react-icons/fa";
import { brand400 } from "../../../../setup/theme/colors";
import { chakraCardBorder } from "../../../../setup/theme/utils/chakraCardBorder";

interface RowProps {
  children?: React.ReactNode;
  boxProps?: BoxProps;
}

const Row = ({ children, boxProps }: RowProps) => {
  return (
    <Box
      borderBottom={"1px"}
      borderColor={"gray.300"}
      bg={"gray.100"}
      w={"100%"}
      h={"50px"}
      borderRadius={"6px 6px 0px 0px"}
      {...boxProps}
    >
      <HStack h={"100%"} px={3}>
        {children}
      </HStack>
    </Box>
  );
};

const GIT_ROWS = ["cluster", "configuration", "documentation"];

const GitHubImage = () => {
  return (
    <Box
      pos={"relative"}
      bg={"white"}
      boxShadow={"md"}
      w={"100%"}
      h={"200px"}
      {...chakraCardBorder}
      rounded={"md"}
      fontSize={"sm"}
    >
      <Row>
        <Avatar bg={brand400} size={"sm"} name="Brain Works" />
        <Text fontWeight={700}>BRAINWORKS</Text>
        <Text display={{ base: "none", sm: "block" }}>
          Alpha release of software
        </Text>
      </Row>
      {GIT_ROWS.map((item, i) => {
        const lastItem = i === GIT_ROWS.length - 1;
        return (
          <Row
            boxProps={{
              bg: "white",
              borderRadius: lastItem ? "0px 0px 8px 8px" : "",
            }}
            key={`git-${i}`}
          >
            <Icon mx={2} as={FaFolder} />
            <Text>{item}</Text>
          </Row>
        );
      })}

      <Icon
        boxShadow={"lg"}
        borderRadius={"100%"}
        bg={"gray.900"}
        p={"1"}
        color={"white"}
        pos={"absolute"}
        bottom={-5}
        right={{ base: "5%", sm: -10 }}
        fontSize={{ base: "70px", sm: "120px" }}
        as={FaGithub}
      />
    </Box>
  );
};

export default GitHubImage;
