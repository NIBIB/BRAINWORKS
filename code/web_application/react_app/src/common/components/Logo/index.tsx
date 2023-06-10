import { Icon } from "@chakra-ui/react";

interface AppProps {
  color?: string;
}

const Logo = (props: AppProps) => {
  return (
    <Icon
      color={props.color ? props.color : "brand"}
      boxSize={10}
      viewBox="-2 -1 50 50"
    >
      <path
        fill="currentColor"
        d="M27.306 19.537a5.502 5.502 0 1 0 7.623-7.938 5.502 5.502 0 0 0-7.623 7.938ZM12.07 35.4a5.502 5.502 0 1 0 7.623-7.937 5.502 5.502 0 0 0-7.622 7.938ZM11.757 19.85a5.502 5.502 0 1 0 7.622-7.936 5.502 5.502 0 0 0-7.623 7.937ZM27.62 35.086a5.502 5.502 0 1 0 7.623-7.937 5.502 5.502 0 0 0-7.622 7.937Z"
      />
    </Icon>
  );
};

export default Logo;
