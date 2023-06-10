import { Box } from "@chakra-ui/react";
import React, { forwardRef } from "react";
import type { BoxProps } from "@chakra-ui/react";

interface AppProps {
  children: React.ReactNode;
  /**
   * `props` - ChakraUI's box properties
   */
  boxProps?: BoxProps;
}

/**
 * Card
 *
 * React component that renders a reusable card component wrapper
 */
const Card = forwardRef<HTMLDivElement, AppProps>(
  ({ children, boxProps }, ref) => {
    return (
      <Box
        border={"1px"}
        borderColor={"gray.200"}
        overflow={"hidden"}
        opacity={"100%"}
        bg={"white"}
        h={"100%"}
        w={"100%"}
        {...boxProps}
        ref={ref}
      >
        {children}
      </Box>
    );
  }
);

export default Card;
