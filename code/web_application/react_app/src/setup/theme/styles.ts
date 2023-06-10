import { mode } from "@chakra-ui/theme-tools";
import { StyleFunctionProps } from "@chakra-ui/theme-tools";

const styles = {
  global: (props: StyleFunctionProps) => ({
    body: {
      bg: mode("gray.50", "gray.900")(props),
    },
    ".highlight": {
      bg: "gray.300",
    },
    ".selected": {
      bg: "rgba(255, 162, 0, 0.45)",
    },
    ".hovered": {
      bg: "rgba(255, 162, 0, 0.45)",
    },
    "#graphAPI-container": {
      iframe: {
        bg: "gray.50",
      },
    },
  }),
};

export default styles;
