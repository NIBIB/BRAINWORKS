import {
  Container,
  Flex,
  Heading,
  HStack,
  Icon,
  VStack,
} from "@chakra-ui/react";
import Card from "common/components/Card";
import React, { ReactNode } from "react";
import { FiArrowLeft } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

interface AppProps {
  title: string;
  desc: string;
  children: ReactNode;
}

const ChangeSettingsCard = ({ title, desc, children }: AppProps) => {
  const navigate = useNavigate();
  return (
    <Flex w="100vw" h="100vh" justify="center" align="center">
      <Container>
        <Card boxProps={{ p: 5, borderRadius: "md" }}>
          <VStack w="100%" align="flex-start" spacing={3}>
            <HStack onClick={() => navigate(-1)} w="100%">
              <Icon as={FiArrowLeft} color="gray.600" />
              <Heading fontWeight={500} size="xs" color="gray.600">
                Back
              </Heading>
            </HStack>
            <Heading size="md">{title}</Heading>
            <Heading size="sm" fontWeight={400} color="gray.600">
              {desc}
            </Heading>
            {children}
          </VStack>
        </Card>
      </Container>
    </Flex>
  );
};

export default ChangeSettingsCard;
