import { Button, ButtonProps } from "@chakra-ui/react";
import { NavLink } from "react-router-dom";
import {
  brand100,
  brand400,
  brand500,
} from "../../../../../setup/theme/colors";

interface AppProps {
  text: string;
  buttonProps?: ButtonProps;
}

const GetStartedButton = ({ text, buttonProps }: AppProps) => {
  return (
    <NavLink to="/signup">
      <Button
        h={50}
        color="white"
        border={"5px solid"}
        borderColor={brand100}
        rounded={"full"}
        px={6}
        bg={brand400}
        _hover={{ bg: brand500 }}
        {...buttonProps}
        width={{ base: "100%", sm: "auto" }}
      >
        {text}
      </Button>
    </NavLink>
  );
};

export default GetStartedButton;
