// theme.ts (tsx file with usage of StyleFunctions, see 4.)
import { extendTheme } from "@chakra-ui/react";
import components from "./components";
import colors from "./colors";
import styles from "./styles";
import config from "./config";

export const theme = extendTheme({
  components,
  colors,
  styles,
  config,
});
