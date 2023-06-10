import { SimpleGrid, SimpleGridProps } from "@chakra-ui/react";
import React from "react";

interface AppProps {
  children: React.ReactNode;
  simpleGridProps?: SimpleGridProps;
}

const FeatureGridLayout = ({ children, simpleGridProps }: AppProps) => {
  return (
    <SimpleGrid
      gap={"50px"}
      px={{ base: 5, sm: 8 }}
      columns={{ base: 1, md: 2 }}
      row={{ base: 2, md: 1 }}
      {...simpleGridProps}
    >
      {children}
    </SimpleGrid>
  );
};

export default FeatureGridLayout;
