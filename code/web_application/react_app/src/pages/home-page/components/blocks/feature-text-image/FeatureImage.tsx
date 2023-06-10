import { Center, VStack } from "@chakra-ui/react";
import React from "react";

interface AppProps {
  image: React.ReactNode;
}

const FeatureImage = ({ image }: AppProps) => {
  const WIDTH = "400px";
  const HEIGHT = "300px";

  return (
    <Center>
      <VStack
        pos={"relative"}
        justify={"center"}
        rounded={"2xl"}
        height={{ base: "auto", md: HEIGHT }}
        w={{ base: "100%", sm: WIDTH }}
      >
        {image}
      </VStack>
    </Center>
  );
};

export default FeatureImage;
