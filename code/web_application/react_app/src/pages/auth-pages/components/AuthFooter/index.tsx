import { VStack } from "@chakra-ui/react";
import { ReactNode } from "react";

interface AppProps {
  children: ReactNode;
}

const AuthFooter = ({ children }: AppProps) => {
  return <VStack mt={5}>{children}</VStack>;
};

export default AuthFooter;
