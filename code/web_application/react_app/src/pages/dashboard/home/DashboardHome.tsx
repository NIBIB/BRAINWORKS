import {
  Button,
  Container,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react";
import React from "react";
import useCurrentUser from "../../../common/hooks/useCurrentUser";

const DashboardHome = () => {
  const { user } = useCurrentUser();

  return (
    <HStack py={50} px={10} justify="space-between">
      <VStack align="flex-start">
        <Heading>Welcome back!</Heading>
        <Text color="gray.500">{user.name}'s Dashboard</Text>
      </VStack>
      <Button>Create visual</Button>
    </HStack>
  );
};

export default DashboardHome;
