import React, { Fragment, ReactNode } from "react";
import {
  IconButton,
  Box,
  CloseButton,
  Flex,
  Icon,
  useColorModeValue,
  Link,
  Drawer,
  DrawerContent,
  useDisclosure,
  BoxProps,
  FlexProps,
  Text,
} from "@chakra-ui/react";
import { FiMenu } from "react-icons/fi";
import { IconType } from "react-icons";
import { brand300, brand400, brand50 } from "../../../setup/theme/colors";
import LogoWithText from "../LogoWithText";
import { useLocation, useNavigate } from "react-router-dom";
import useCurrentUser from "../../hooks/useCurrentUser";

export interface SideBarGroups {
  title: string;
  items: SidebarItemProps[];
}

interface FilterSidebarProps {
  sidebarItems: SideBarGroups[];
  initalState: string;
  children: ReactNode;
}

export interface SidebarItemProps {
  name: string;
  icon: IconType;
  component?: ReactNode;
  path: string;
  admin?: boolean;
}

/**
 * FilterSidebar
 *
 * Renders sidebar and child node
 */
export default function FilterSidebar({
  children,
  sidebarItems,
  initalState,
}: FilterSidebarProps) {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <Flex>
      <SidebarContent
        onClose={() => onClose}
        display={{ base: "none", md: "block" }}
        sidebarItems={sidebarItems}
      />
      <Drawer
        autoFocus={false}
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
        size="full"
      >
        <DrawerContent>
          <SidebarContent sidebarItems={sidebarItems} onClose={onClose} />
        </DrawerContent>
      </Drawer>
      <MobileNav display={{ base: "flex", md: "none" }} onOpen={onOpen} />
      <Box w="100%" minHeight="100vh" pl={{ base: 0, md: 60 }}>
        {children}
      </Box>
    </Flex>
  );
}

interface SidebarContentProps extends BoxProps {
  onClose: () => void;
  sidebarItems: SideBarGroups[];
}

/**
 * SideBar content
 *
 * Sidebar styling
 */
const SidebarContent = ({
  onClose,
  sidebarItems,
  ...rest
}: SidebarContentProps) => {
  const { user } = useCurrentUser();

  return (
    <Box
      w={{ base: "full", md: 60 }}
      pos={"fixed"}
      minHeight="100vh"
      maxH={"100%"}
      borderRight={"1px solid"}
      borderColor={"gray.200"}
      bg="white"
      {...rest}
    >
      {sidebarItems.map((item, i) => (
        <Fragment key={i}>
          <Flex
            h="20"
            alignItems="center"
            mx="8"
            justifyContent="space-between"
          >
            <LogoWithText />
            <CloseButton
              display={{ base: "flex", md: "none" }}
              onClick={onClose}
            />
          </Flex>

          {item.items.map((link) => {
            if (link.admin && !user.admin) {
              return null;
            }
            return (
              <NavItem
                name={link.name}
                key={link.name}
                icon={link.icon}
                path={link.path}
              >
                <Text fontSize={"sm"}>{link.name}</Text>
              </NavItem>
            );
          })}
        </Fragment>
      ))}
    </Box>
  );
};

interface NavItemProps extends FlexProps {
  icon: IconType;
  children: ReactNode;
  name: string;
  path: string;
}

/**
 * NavItem
 *
 * Styles for each individual navigation item on the sidebar
 */
const NavItem = ({ icon, children, name, path, ...rest }: NavItemProps) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Link
      style={{ textDecoration: "none" }}
      _focus={{ boxShadow: "none" }}
      onClick={() => {
        navigate(path);
      }}
    >
      <Flex
        align="center"
        p={4}
        mx={4}
        role="group"
        cursor="pointer"
        color={location.pathname === path ? brand400 : ""}
        _hover={{
          color: brand300,
        }}
        bg={location.pathname === path ? brand50 : ""}
        borderRadius="lg"
        {...rest}
      >
        {icon && (
          <Icon
            mr="4"
            fontSize="16"
            _groupHover={{
              color: brand300,
            }}
            as={icon}
          />
        )}
        {children}
      </Flex>
    </Link>
  );
};

interface MobileProps extends FlexProps {
  onOpen: () => void;
}
/**
 * MobileNav
 *
 * Shows up when screen is mobile sized
 */
const MobileNav = ({ onOpen, ...rest }: MobileProps) => {
  return (
    <Flex
      ml={{ base: 0, md: 60 }}
      px={{ base: 4, md: 24 }}
      height="20"
      alignItems="center"
      bg={useColorModeValue("white", "gray.900")}
      justifyContent="flex-start"
      {...rest}
    >
      <IconButton
        variant="outline"
        onClick={onOpen}
        aria-label="open menu"
        icon={<FiMenu />}
      />
    </Flex>
  );
};
