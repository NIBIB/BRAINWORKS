import {
  Box,
  Card,
  CardBody,
  Flex,
  useMediaQuery,
  VStack,
} from "@chakra-ui/react";
import { ReactNode } from "react";

interface AppProps {
  children: ReactNode;
}

/**
 * AuthCard
 *
 * React component that wraps around auth elements, centering it and giving it a fixed width
 */
const AuthCard = ({ children }: AppProps) => {
  const [isSmallerThan500] = useMediaQuery("(max-width: 500px)");
  return (
    <Flex w="100%" h="90vh" justify="center" align="center">
      <Card w={isSmallerThan500 ? "90%" : "450px"} p={5} bg="white">
        <CardBody>{children}</CardBody>
      </Card>
    </Flex>
  );
};

export default AuthCard;
