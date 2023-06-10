import { Link, LinkProps } from "@chakra-ui/react";
import { Link as ReactRouterLink } from "react-router-dom";

interface AppProps {
  text: string;
  link: string;
  linkProps?: LinkProps;
}
const RouterLink = ({ text, link, linkProps }: AppProps) => {
  return (
    <Link color="blue.600" as={ReactRouterLink} to={link} {...linkProps}>
      {text}
    </Link>
  );
};

export default RouterLink;
