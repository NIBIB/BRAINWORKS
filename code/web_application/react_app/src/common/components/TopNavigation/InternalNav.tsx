import {
  Avatar,
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
} from "@chakra-ui/react";
import useCurrentUser from "common/hooks/useCurrentUser";
import { FiLogOut, FiSettings } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

/**
 * Internal Navigation
 *
 * React component that displays all routing
 */
const InternalNav = () => {
  const { user, logOut } = useCurrentUser();
  const navigate = useNavigate();

  const handleLogOut = async () => {
    await logOut();
    navigate("/");
  };

  const handleSettings = async () => {
    navigate("/settings");
  };

  return (
    <Menu>
      <MenuButton
        as={Button}
        rounded={"full"}
        variant={"link"}
        cursor={"pointer"}
        minW={0}
      >
        <Avatar size={"sm"} name={user?.name} />
      </MenuButton>
      <MenuList>
        <MenuItem icon={<FiSettings />} onClick={handleSettings}>
          Settings
        </MenuItem>
        <MenuDivider />
        <MenuItem icon={<FiLogOut />} onClick={handleLogOut}>
          Sign out
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

export default InternalNav;
