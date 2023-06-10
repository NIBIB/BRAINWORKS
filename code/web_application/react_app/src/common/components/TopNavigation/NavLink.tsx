import { Link } from "@chakra-ui/react";
import { Link as ReactRouterLink, useLocation } from "react-router-dom";
import { LinkProps } from "@chakra-ui/react";
import { brand400 } from "../../../setup/theme/colors";

export interface AppProps {
  path: string[];
  children?: React.ReactNode;
  linkProps?: LinkProps;
  underline?: boolean;
}

/**
 * NavLink
 *
 * React component that
 */
const NavLink = ({ path, children, linkProps, underline }: AppProps) => {
  const location = useLocation();
  const showUnderline = underline && path.includes(location.pathname);

  return (
    <Link
      as={ReactRouterLink}
      _hover={{
        textDecoration: "none",
        color: brand400,
      }}
      to={path[0]}
      {...linkProps}
      color={showUnderline ? brand400 : ""}
    >
      {children}
    </Link>
  );
};

export default NavLink;
