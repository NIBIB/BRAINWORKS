import { Link, LinkProps, TextProps } from "@chakra-ui/react";

interface AppProps {
  onClick: () => void;
  text: string;
  linkProps?: LinkProps;
  textProps?: TextProps;
}

/**
 * ActionLink
 *
 * React component that renders a ChakraUI link with an on click property
 */
const ActionLink = ({ onClick, text, linkProps, textProps }: AppProps) => {
  return (
    <Link as="span" color="blue.600" onClick={onClick} {...linkProps}>
      {text}
    </Link>
  );
};

export default ActionLink;
