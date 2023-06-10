import { chakra, TransitionProps } from "@chakra-ui/react";
import { motion, isValidMotionProp } from "framer-motion";
import type { BoxProps } from "@chakra-ui/react";
import { brand400 } from "../../../../../setup/theme/colors";

const ChakraBox = chakra(motion.div, {
  shouldForwardProp: (prop) => isValidMotionProp(prop) || prop === "children",
});

interface AppProps {
  boxProps?: BoxProps;
  duration: number;
  transitionProps?: TransitionProps;
}

const BouncingBall = ({ duration, boxProps }: AppProps) => {
  return (
    <ChakraBox
      animate={{
        scale: [1, 1.05, 1],
        translateY: [0, -10, 10, 0],
      }}
      // @ts-ignore no problem in operation, although type error appears.
      transition={{
        duration: duration,
        ease: "easeInOut",
        repeat: Infinity,
        repeatType: "loop",
      }}
      padding="2"
      bg={brand400}
      display="flex"
      justifyContent="center"
      alignItems="center"
      width="100px"
      height="100px"
      borderRadius="50%"
      pos={"absolute"}
      {...boxProps}
    ></ChakraBox>
  );
};

export default BouncingBall;
