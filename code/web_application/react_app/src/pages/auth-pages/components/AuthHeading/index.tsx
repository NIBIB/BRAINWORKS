import { Heading, Text, VStack } from "@chakra-ui/react";

interface AppProps {
  title: string;
  desc: string;
}

const AuthHeading = ({ title, desc }: AppProps) => {
  return (
    <VStack mb={5}>
      <Heading w="100%" textAlign="center">
        {title}
      </Heading>
      <Text textAlign="center" color="gray.600">
        {desc}
      </Text>
    </VStack>
  );
};

export default AuthHeading;
