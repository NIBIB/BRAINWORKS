import { Flex, Heading, Text, VStack } from "@chakra-ui/react";

/**
 * Invalid Token
 *
 * React component that displays when an invalid token is given
 */
const InvalidToken = () => {
  return (
    <Flex h="90vh" align="center" justify="center">
      <VStack maxW="xl" textAlign="center">
        <Heading>Invalid link.</Heading>
        <Text color="gray.500">
          Link may be expired or copied incorrectly. Please make sure you copied
          the correct link from your email. If that doesn't work try requesting
          another one.
        </Text>
      </VStack>
    </Flex>
  );
};

export default InvalidToken;
